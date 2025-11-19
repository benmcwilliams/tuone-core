#from cmath import phase
import logging
import re
import sys; sys.path.append("..")
from pymongo import UpdateOne
from datetime import datetime
import pandas as pd
from mongo_client import facilities_collection

## main logic should be updated to read from phases (or drop main...)

STATUS_NORMALIZE = {
    "ongoing": "under construction",
    "completed": "operational",
}
STATUS_ORDER = ["cancelled", "paused", "operational", "under construction", "announced", "unclear"]
STATUS_RANK = {status: i for i, status in enumerate(STATUS_ORDER)}

PAUSELIKE = {"cancelled", "paused"}  # facility events can only vote for pauses or cancellations
INV_PAUSELIKE = PAUSELIKE | {"under construction", "announced"}

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
    ''' 
    Safely evaluate all phase numbers as integers, even if they are read in as strings. 
    '''
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

def _is_relevant_event(c: dict, phase_num: int | None) -> bool:
    """
    Returns a boolean for whether an event should be included or not.
    Basic filter: valid status, not ignored, has date, and matches phase if specified.
    """
    if c.get("status") not in STATUS_ORDER:
        return False
    if phase_is_ignored(c):
        return False
    if not c.get("date"):
        return False

    # Phase filter
    if phase_num is None:
        return True
    pn = phase_num_int(c)
    return pn is not None and pn == phase_num

def _is_status_eligible(c: dict) -> bool:
    """Who gets to 'vote' for STATUS."""
    et = c.get("event_type")
    st = c.get("status")

    if et == "capacity":
        return True  # capacity can always vote

    if et in {"facility"}:
        return st in PAUSELIKE          # only paused/cancelled can vote from facility

    if et in {"investment"}:
        return st in INV_PAUSELIKE      # investments can vote also if ongoing / announced but not completed

    # other event types (e.g., operations/construction) may vote
    return True

def normalize_pl2(vals):
    return sorted({str(v).strip() for v in (vals or []) if v is not None and str(v).strip()})

def events_product_lv2_union(events: list) -> list[str]:
    """
    Collect union of product_lv2 from non-ignored events
    """
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

    - Chooses the strongest status (lowest STATUS_RANK, then most recent date).
    - Capacity:
        if additional == False → take as total
        if additional == True  → add to prev_capacity
    - Investment:
        if is_total == True  → take as total
        if is_total == False → add to prev_investment
    - Adds earliest milestone dates (announce, under construction, operational).
    """

    # 1. filter for relevant phase events (valid data and user has not set ignored)
    phase_events = [c for c in events if _is_relevant_event(c, phase_num)]
    if not phase_events:
        return None

    # 2. sort events by i) status strength; ii) most recent date (could prefer capacity > investment > facility?)
    sorted_events = sorted(
        phase_events,
        key=lambda c: (
            STATUS_RANK[c["status"]], 
            -parse_date(c["date"]).timestamp())
    )

    # --------------- set STATUS -----------------
    # only consider facility and investment event types for paused or cancellation events
    status_rows = [c for c in sorted_events if _is_status_eligible(c)]
    best_status_row = (status_rows[0] if status_rows else sorted_events[0])

    # ------------- set CAPACITIES ----------------
    cap_rows = [
        c for c in phase_events
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
    capacity_article_id = None  # initialise

    if cap_rows:
        latest = cap_rows[0]
        v = latest.get("capacity")          # the value
        add = latest.get("additional")      # is it an explicitly additional value
        capacity_article_id = latest.get("articleID")

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
        [c for c in phase_events if c.get("event_type") != "facility" and c.get("investment") is not None],
        key=lambda c: (
            STATUS_RANK.get(c.get("status"), len(STATUS_ORDER)),
            -parse_date(c["date"]).timestamp(),
            0 if c.get("is_total") else 1
        )
    )

    # set the backup imputed investments
    imputed_rows = sorted(
        [c for c in phase_events if c.get("investment_imputed") is not None],
        key=lambda c: (
            STATUS_RANK.get(c.get("status"), len(STATUS_ORDER)),
            -parse_date(c["date"]).timestamp(),
            0 if c.get("is_total") else 1
        )
    )

    investment = None                       # the cumulative investment
    phase_investment = None                 # the investment specific to this phase
    investment_was_imputed = False          # did we have to impute the investment?

    # if there are real investments, store the best one
    if inv_rows:
        latest = inv_rows[0]
        v = latest.get("investment")
        total = latest.get("is_total")
        investment_article_id = latest.get("articleID")

    # otherwise, take the best implied investment
    elif imputed_rows:
        latest = imputed_rows[0]
        v = latest.get("investment_imputed")
        total = latest.get("is_total")
        investment_article_id = latest.get("articleID")
        investment_was_imputed = True

    else:
        latest = None
        v = None
        total = None
        investment_article_id = None

    if latest:
        if total is True:
            # explicit total after this phase
            if prev_investment is not None:
                phase_investment = max(v - prev_investment, 0)  # set phase_investment to the is_total value - prev_investment
            else:
                phase_investment = v
            investment = v   # set cumulative investment to the is_total value

        elif total is False:
            phase_investment = v                            # not total, set as phase investment
            investment = (prev_investment or 0) + v         # not total, add to cumulative investments

        # --- recalculate implied investment to better reflect specific project situation ---
        if investment_was_imputed and prev_investment is not None:
            if prev_capacity and capacity and prev_capacity > 0:
                implied_ratio = prev_investment / prev_capacity
                phase_investment = max((capacity - prev_capacity) * implied_ratio, 0)
                investment = prev_investment + phase_investment

    summary = {
        "status": best_status_row["status"],
        "status_article_id": best_status_row.get("articleID"),
        "phase_capacity": phase_capacity,
        "capacity": capacity,
        "capacity_article_id": capacity_article_id,
        "phase_investment": phase_investment,
        "investment": investment,
        "investment_was_imputed": investment_was_imputed,
        "investment_article_id": investment_article_id,
        "source_date": best_status_row["date"],
    }
    
    # ------------- set CHRONOLOGY ----------------
    # add chronological milestone dates with two rules:
    # 1) construction can count as announcement if earlier (or announcement missing)
    # 2) if construction exists and operational is missing, set operational = construction + 2 years
    chron = sorted(status_rows, key=lambda c: parse_date(c["date"]))
    # we use status_rows (ie investment and facilities can vote only if paused | cancelled)
    # perhaps want to allow investments to vote for "ongoing" or "announced". Seems "completed" is the buggy one. 

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
        summary["announced_article_id"] = ann.get("articleID")
    if uc:
        summary["under_construction_on"] = uc["date"]
        summary["under_construction_article_id"] = uc.get("articleID")

    if op:
        summary["operational_on"] = op["date"]
        summary["operational_article_id"] = op.get("articleID")
    elif uc:
        # Rule 2: no operational date → set to construction + 3 years
        uc_dt = parse_date(uc["date"])
        if pd.notna(uc_dt):
            op_dt = uc_dt + pd.DateOffset(years=3)
            summary["operational_on"] = op_dt.strftime("%Y-%m-%d")

    # --- Rule 3: backfill earlier milestones from an operational date ---
    if op:
        op_dt = parse_date(op["date"])
        if pd.notna(op_dt):
            ann_dt = parse_date(ann["date"]) if ann else None
            uc_dt  = parse_date(uc["date"]) if uc else None

            # Case A: both missing → set both to (op - 3 years)
            if ann_dt is None and uc_dt is None:
                backfill = (op_dt - pd.DateOffset(years=3)).strftime("%Y-%m-%d")
                summary["announced_on"] = backfill
                summary["under_construction_on"] = backfill

            # Case B: announced exists but construction missing
            elif ann_dt is not None and uc_dt is None:
                two_years_before = op_dt - pd.DateOffset(years=3)
                use_dt = ann_dt if ann_dt > two_years_before else two_years_before
                summary["under_construction_on"] = use_dt.strftime("%Y-%m-%d")

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

        # ---------- build "main" summary from phases list ----------
        if phases_list:
            selected = None
            prev_oper = None            # a previously operational phase
            for ph in phases_list:
                st = ph.get("status")
                # if the current phase is operational move on (but store as latest operational)
                if st == "operational":
                    prev_oper = ph  # keep latest operational seen so far
                    continue
                #  non-operational phase encountered. stop and take this phase, or a previous operational if exists.
                selected = prev_oper if prev_oper is not None else ph
                break
            else:
                # never hit a non-operational → take the last phase
                selected = phases_list[-1]

            # earliest dates across all phases
            def _earliest(phases, key):
                dts = [parse_date(p.get(key)) for p in phases if p.get(key)]
                dts = [d for d in dts if pd.notna(d)]
                return min(dts).strftime("%Y-%m-%d") if dts else None

            main_summary = {
                "status": selected.get("status"),
                "capacity": selected.get("capacity"),
                "investment": selected.get("investment"),
                "investment_was_imputed": selected.get("investment_was_imputed", False),
                "announced_on": _earliest(phases_list, "announced_on"),
                "under_construction_on": _earliest(phases_list, "under_construction_on"),
                "operational_on": _earliest(phases_list, "operational_on"),
                "main_from_phase_num": selected.get("phase_num"),  # optional provenance; drop if you prefer
            }

            update_fields["main"] = main_summary
        else:
            # no phases → ensure main is unset to avoid staleness
            if "main" in doc:
                unset_fields["main"] = ""

        # Queue update with both $set and $unset. With $set we are always overwriting.
        if update_fields or unset_fields:
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