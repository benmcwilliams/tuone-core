import logging
import sys; sys.path.append("..")
from pymongo import UpdateOne
from datetime import datetime
import pandas as pd  # for robust datetime handling
from mongo_client import facilities_collection

## consider main.investment and main.capacity logic. If not is_total / additional. 

STATUS_NORMALIZE = {
    "ongoing": "under construction",
    "completed": "operational",
}
STATUS_ORDER = ["cancelled", "paused", "operational", "under construction", "announced", "unclear"]
STATUS_RANK = {status: i for i, status in enumerate(STATUS_ORDER)}

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
    return v if isinstance(v, int) else None

def normalize_pl2(vals):
    return sorted({str(v).strip() for v in (vals or []) if v is not None and str(v).strip()})

# NEW: collect union of product_lv2 from NON-IGNORED events
def events_product_lv2_union(events: list) -> list[str]:
    acc = set()
    for ev in events or []:
        if phase_is_ignored(ev):
            continue  # skip ignored events entirely
        for v in (ev.get("product_lv2") or []):
            if v is None:
                continue
            s = str(v).strip()
            if s:
                acc.add(s)
    return sorted(acc)

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

    # filter for relevant phase
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
     
    # sort by status strength, then by most recent date
    sorted_events = sorted(
        phase_caps,
        key=lambda c: (STATUS_RANK[c["status"]], -parse_date(c["date"]).timestamp())
    )
    best = sorted_events[0]

    # Status should be decided by CAPACITY rows only (fallback to all if none)
    status_rows = [c for c in phase_caps if c.get("event_type") == "capacity"]
    if not status_rows:
        status_rows = phase_caps  # rare fallback: no capacity evidence exists

    sorted_status = sorted(
        status_rows,
        key=lambda c: (
            STATUS_RANK.get(c.get("status"), len(STATUS_ORDER)),
            -parse_date(c["date"]).timestamp()
        )
    )
    best_status_row = sorted_status[0]

    # ---- Capacity logic ----
    cap_rows = [
        c for c in phase_caps
        if c.get("event_type") == "capacity" 
        and c.get("capacity") is not None
    ]

    # Use same priority as 'best': stronger status first, then most-recent date
    # Optional extra tiebreaker: prefer totals over additionals on equal status/date
    cap_rows.sort(
        key=lambda c: (
            STATUS_RANK.get(c.get("status"), len(STATUS_ORDER)),           # status strength
            -parse_date(c["date"]).timestamp(),                            # recency
            0 if c.get("additional") is False else 1                       # prefer totals
        )
    )

    capacity = None
    if cap_rows:
        latest = cap_rows[0]
        if latest.get("additional") is True and prev_capacity is not None:
            capacity = prev_capacity + latest["capacity"]
        else:
            capacity = latest["capacity"]

    # Order all investment rows in this phase (stronger status, newer date, totals before incrementals)
    inv_rows = sorted(
        [c for c in phase_caps if c.get("event_type") != "facility" and c.get("investment") is not None],
        key=lambda c: (
            STATUS_RANK.get(c.get("status"), len(STATUS_ORDER)),
            -parse_date(c["date"]).timestamp(),
            0 if c.get("is_total") else 1
        )
    )

    imputed_rows = sorted(
        [c for c in phase_caps if c.get("investment_imputed") is not None],
        key=lambda c: (
            STATUS_RANK.get(c.get("status"), len(STATUS_ORDER)),
            -parse_date(c["date"]).timestamp(),
            0 if c.get("is_total") else 1
        )
    )

    investment, investment_was_imputed = None, False

    if inv_rows:  # take the best real investment
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
        "capacity": capacity,
        "investment": investment, # update this to take any "investment" from across the phase
        "investment_was_imputed": investment_was_imputed,
        "source_date": best["date"],
    }

    # add chronological milestone dates (earliest date each milestone is mentioned)
    for milestone in ["announced", "under construction", "operational"]:
        first = next(
            (c for c in sorted(phase_caps, key=lambda c: parse_date(c["date"]))
             if c["status"] == milestone),
            None
        )
        if first:
            summary[f"{milestone.replace(' ', '_')}_on"] = first["date"]

    return summary

def compute_summaries():
    logging.info("🚀 Starting summary updates for main, phase 1 and phase 2...")

    updates = []

    for doc in facilities_collection.find({}):
        events = doc.get("events", [])
        if not events:
            continue

        # normalize statuses (to compare investments and capacities)
        for c in events:
            if c.get("status") in STATUS_NORMALIZE:
                c["status"] = STATUS_NORMALIZE[c["status"]]

        update_fields = {}

        # ---------- derive facility product_lv2 from NON-IGNORED events ----------
        current_pl2 = normalize_pl2(doc.get("product_lv2"))
        events_pl2 = events_product_lv2_union(events)  # skips "ignore"
        if events_pl2 != current_pl2:
            update_fields["product_lv2"] = events_pl2
        # ------------------------------------------------------------------------

        # unique phase_num mentioned in the events, should be robust to string "ignore"
        phases = sorted({pn for c in events if not phase_is_ignored(c) and (pn := phase_num_int(c)) is not None})  

        # build summaries for each phase and store as phase_1, phase_2, etc (using previous phase capacity/investment to increment)
        prev_capacity, prev_investment = None, None
        for p in phases:
            summary = build_phase_summary(events, p, prev_capacity, prev_investment)
            if summary:
                update_fields[f"phase_{p}"] = summary
                # update rolling totals
                if summary.get("capacity") is not None:
                    prev_capacity = summary["capacity"]
                if summary.get("investment") is not None:
                    prev_investment = summary["investment"]

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

                # ------------------------- REMOVING STALE PHASE SUMMARIES - MUCH CLEANER WHEN WE MOVE TO A LIST OF PHASES -------------------------
        # Remove stale phase_* keys that no longer exist this run
        existing_phase_keys = [k for k in doc.keys() if k.startswith("phase_")]
        existing_phase_nums = set()
        for k in existing_phase_keys:
            try:
                existing_phase_nums.add(int(k.split("_", 1)[1]))
            except Exception:
                pass

        current_phase_nums = set(phases)
        stale_phase_nums = existing_phase_nums - current_phase_nums

        unset_fields = {f"phase_{n}": "" for n in stale_phase_nums}

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