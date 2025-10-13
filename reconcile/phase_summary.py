from cmath import phase
import logging
import re
import sys; sys.path.append("..")
from pymongo import UpdateOne
from datetime import datetime
import pandas as pd  # for robust datetime handling
from mongo_client import facilities_collection

## main logic should be updated to read from phases (or drop main...)

STATUS_NORMALIZE = {
    "ongoing": "under construction",
    "completed": "operational",
}
STATUS_ORDER = ["cancelled", "paused", "operational", "under construction", "announced", "unclear"]
STATUS_RANK = {status: i for i, status in enumerate(STATUS_ORDER)}

# --------- helpers -------------

def parse_date(date_str):
    try:
        return pd.to_datetime(date_str)
    except Exception:
        return pd.NaT

def phase_is_ignored(ev: dict) -> bool:
    v = ev.get("phase_num")
    return isinstance(v, str) and v.strip().lower() == "ignore"

def phase_num_int(ev: dict) -> int | None:
    v = ev.get("phase_num")
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s == "ignore":
            return None
        if re.fullmatch(r"\d+", s):  # accepts "2", " 2 ", "02"
            return int(s)
    return None

def normalize_pl2(vals):
    return sorted({str(v).strip() for v in (vals or []) if v is not None and str(v).strip()})

# collect union of product_lv2 from NON-IGNORED events
def events_product_lv2_union(events: list) -> list[str]:
    acc = set()

    def _iter_pl2(val):
        # normalize product_lv2 to an iterable of strings
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return []
        if isinstance(val, (list, tuple, set)):
            return val
        return [val]  # single string/scalar

    for ev in events or []:
        if phase_is_ignored(ev):
            continue
        for v in _iter_pl2(ev.get("product_lv2")):
            if v is None:
                continue
            s = str(v).strip()
            if s:
                acc.add(s)

    return sorted(acc)

# ---------- main logic ------------

def build_phase_summary(events: list, phase_num: int | None, prev_capacity=None, prev_investment=None) -> dict | None:

    """
    Build a summary for one phase_num (or all events if phase=None).

    Build a summary for one phase_num (or all events if phase=None).

    - Chooses the strongest status (lowest STATUS_RANK, then most recent date).
    - Capacity:
        if additional == False → take as total
        if additional == True  → add to prev_capacity
    - Investment:
        if is_total == True  → take as total
        if is_total == False → add to prev_investment
    - Adds earliest milestone dates (announce, under construction, operational).
    """

    # filter for relevant phases (not ignored, not facility-level)
    phase_caps = [
        c for c in events
        if c.get("status") in STATUS_ORDER
        and c.get("event_type") != "facility"   # ignore facility events (improve this to consider as a vote for STATUS only)
        and not phase_is_ignored(c)
        and (phase_num is None or (phase_num_int(c) is not None and phase_num_int(c) == phase_num)) # if main, then phase_num = None & skip, otherwise filter
        and c.get("date")
    ]
    if not phase_caps:
        return None
     
    # sort by 1) status strength; 2) most recent date
    sorted_events = sorted(
        phase_caps,
        key=lambda c: (
            STATUS_RANK[c["status"]], 
            -parse_date(c["date"]).timestamp())
    )
    best = sorted_events[0]

    # --------------- set STATUS -----------------
    # sorted by CAPACITY rows as a priority (fallback to all)
    status_rows = [c for c in sorted_events if c.get("event_type") == "capacity"]
    if not status_rows:
        status_rows = sorted_events  # fallback to any event if no capacity evidence
    best_status_row = status_rows[0]

    # ------------- set CAPACITIES ----------------
    cap_rows = [
        c for c in phase_caps
        if c.get("event_type") == "capacity" 
        and c.get("capacity") is not None
    ]
    # Sort: stronger status first, then most-recent date, totals preferred over additionals on tiebreak
    cap_rows.sort(
        key=lambda c: (
            STATUS_RANK.get(c.get("status"), len(STATUS_ORDER)),           # status strength
            -parse_date(c["date"]).timestamp(),                            # recency
            0 if c.get("additional") is False else 1                       # prefer totals
        )
    )

    capacity = None             # the cumulative capacity
    phase_capacity = None       # capacity specific to this phase 

    if cap_rows:
        latest = cap_rows[0]
        v = latest.get("capacity")          # the value
        add = latest.get("additional")      # is it an explicitly additional value

        if add is True:
            # explicit incremental update
            phase_capacity = v
            capacity = (prev_capacity or 0) + v

        elif add is False:
            # explicit total after this phase
            if prev_capacity is not None:
                phase_capacity = max(v - prev_capacity, 0)
            else:
                phase_capacity = v
            capacity = v

    # ------------- set INVESTMENTS ----------------
    # set real investments
    inv_rows = sorted(
        [c for c in phase_caps if c.get("event_type") != "facility" and c.get("investment") is not None],
        key=lambda c: (
            STATUS_RANK.get(c.get("status"), len(STATUS_ORDER)),
            -parse_date(c["date"]).timestamp(),
            0 if c.get("is_total") else 1
        )
    )

    # set the backup imputed investments
    imputed_rows = sorted(
        [c for c in phase_caps if c.get("investment_imputed") is not None],
        key=lambda c: (
            STATUS_RANK.get(c.get("status"), len(STATUS_ORDER)),
            -parse_date(c["date"]).timestamp(),
            0 if c.get("is_total") else 1
        )
    )

    investment, investment_was_imputed = None, False

    # if there are real investments, take the best one
    if inv_rows:
        row = inv_rows[0]
        if row.get("is_total") is False and prev_investment is not None:
            investment = prev_investment + row["investment"]
        else:
            investment = row["investment"]
    elif imputed_rows:  # fallback to imputed
        row = imputed_rows[0]
        if row.get("is_total") is False and prev_investment is not None:
            investment = prev_investment + row["investment_imputed"]
        else:
            investment = row["investment_imputed"]
        investment_was_imputed = True

    summary = {
        "status": best_status_row["status"],
        "phase_capacity": phase_capacity,
        "capacity": capacity,
        "investment": investment,
        "investment_was_imputed": investment_was_imputed,
        "source_date": best["date"],
    }

    # ------------- set CHRONOLOGY ----------------
    # add chronological milestone dates with two rules:
    # 1) construction can count as announcement if earlier (or announcement missing)
    # 2) if construction exists and operational is missing, set operational = construction + 2 years
    chron = sorted(phase_caps, key=lambda c: parse_date(c["date"]))

    ann = next((c for c in chron if c["status"] == "announced"), None)
    uc  = next((c for c in chron if c["status"] == "under construction"), None)
    op  = next((c for c in chron if c["status"] == "operational"), None)

    # Rule 1: construction implies announcement if earlier or announcement missing
    if uc:
        uc_dt = parse_date(uc["date"])
        if (ann is None) or pd.isna(parse_date(ann["date"])) or (
            pd.notna(uc_dt) and uc_dt < parse_date(ann["date"])
        ):
            ann = uc

    if ann:
        summary["announced_on"] = ann["date"]
    if uc:
        summary["under_construction_on"] = uc["date"]

    if op:
        summary["operational_on"] = op["date"]
    elif uc:
        # Rule 2: no operational date → set to construction + 2 years
        uc_dt = parse_date(uc["date"])
        if pd.notna(uc_dt):
            op_dt = uc_dt + pd.DateOffset(years=2)
            summary["operational_on"] = op_dt.strftime("%Y-%m-%d")

    return summary

# ------ main ---------

def compute_summaries():
    logging.info("🚀 Starting summary updates for main, phase 1 and phase 2...")

    updates = []

    for doc in facilities_collection.find({}):
        events = doc.get("events", [])
        if not events:
            continue

        update_fields: dict = {}
        unset_fields: dict = {}
        main_summary = None  #

        # normalize statuses (to compare investments and capacities)
        for c in events:
            if c.get("status") in STATUS_NORMALIZE:
                c["status"] = STATUS_NORMALIZE[c["status"]]

        # ---------- derive facility product_lv2 from NON-IGNORED events ----------
        current_pl2 = normalize_pl2(doc.get("product_lv2"))
        events_pl2 = events_product_lv2_union(events)  # skips "ignore"
        if events_pl2 != current_pl2:
            update_fields["product_lv2"] = events_pl2
        # ------------------------------------------------------------------------

        # unique phase_num mentioned in the events, should be robust to string "ignore"
        phases = sorted({pn for c in events if not phase_is_ignored(c) and (pn := phase_num_int(c)) is not None})  

        # build summaries for each phase and store as a list under 'phases'
        phases_list = []
        prev_capacity, prev_investment = None, None
        for p in phases:
            summary = build_phase_summary(events, p, prev_capacity, prev_investment)
            if summary:
                # do not persist the helper field 'source_date' inside each phase object
                phase_obj = {"phase_num": p, **{k: v for k, v in summary.items() if k != "source_date"}}
                phases_list.append(phase_obj)

                # update rolling totals
                if summary.get("capacity") is not None:
                    prev_capacity = summary["capacity"]
                if summary.get("investment") is not None:
                    prev_investment = summary["investment"]

        update_fields["phases"] = phases_list

        # build the "main" summary (phase=None means all events)
        main_summary = build_phase_summary(events, phase_num=None)
        if main_summary:

            # --- facility override (can only update a cancelled or paused status) ---
            fac_status_info = doc.get("latest_factory_status") or {}
            fac_status = fac_status_info.get("status")
            fac_date = parse_date(fac_status_info.get("date") or fac_status_info.get("date_str"))

            if fac_status in STATUS_NORMALIZE:
                fac_status = STATUS_NORMALIZE[fac_status]

            if fac_status in STATUS_ORDER and fac_status in {"cancelled", "paused"}:
                main_status = main_summary.get("status")
                main_date = parse_date(main_summary.get("source_date"))

                # decide override if stronger status OR newer date (maybe this should be AND)
                if (
                    (main_status and STATUS_RANK[fac_status] < STATUS_RANK[main_status])
                    or (pd.notna(fac_date) and pd.notna(main_date) and fac_date > main_date)
                ):
                    main_summary["status"] = fac_status
                    main_summary["overridden_by"] = "latest_factory_status"

            # remove helper field before saving
            main_summary.pop("source_date", None)

            update_fields["main"] = main_summary
            
        # If no 'main' summary was produced this run but 'main' exists in DB, unset it to avoid staleness.
        if main_summary is None and "main" in doc:
            unset_fields["main"] = ""

        # Queue update with both $set and $unset (only if they have content)
        if update_fields or unset_fields:  # CHANGED: include unsets-only updates
            update_op = {}
            if update_fields:
                update_op["$set"] = update_fields
            if unset_fields:
                update_op["$unset"] = unset_fields  # CHANGED: remove stale phases/main
            updates.append(UpdateOne({"_id": doc["_id"]}, update_op))

    if updates:
        result = facilities_collection.bulk_write(updates)
        logging.info(f"✅ Updated summaries for {result.modified_count} facilities.")
    else:
        logging.info("⚠️ No facilities needed updates.")

if __name__ == "__main__":
    compute_summaries()