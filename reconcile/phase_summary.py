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
        and (phase_num is None or int(c.get("phase_num", -1)) == phase_num)   # if main, then phase_num = None & skip, otherwise filter
        # cast to -1 and ignore if phase_num is missing
        and c.get("date")
    ]
    if not phase_caps:
        return None

    # sort by status strength, then by most recent date
    sorted_caps = sorted(
        phase_caps,
        key=lambda c: (STATUS_RANK[c["status"]], -parse_date(c["date"]).timestamp())
    )
    best = sorted_caps[0]

    # ---- Capacity logic ---- (# PERHAPS UPDATE LOGIC TO ASSUME THERE IS NO GOOD CAPACITY IN INVESTMENT ROW)
    cap_rows = [c for c in phase_caps if c.get("event_type") == "capacity" and c.get("capacity") is not None]
    cap_rows.sort(key=lambda c: parse_date(c["date"]), reverse=True)
    capacity = None
    if cap_rows:
        latest = cap_rows[0]
        if latest.get("additional") is True and prev_capacity is not None:
            capacity = prev_capacity + latest["capacity"]
        else:
            capacity = latest["capacity"]

    summary = {
        "status": best["status"],
        "capacity": capacity,
        "investment": best["investment"],
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

        phases = sorted({int(c.get("phase_num")) for c in events if c.get("phase_num") is not None})  # unique phase_num mentioned in the events

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

            # --- facility override (status only) ---
            fac_status_info = doc.get("latest_factory_status") or {}
            fac_status = fac_status_info.get("status")
            fac_date = parse_date(fac_status_info.get("date") or fac_status_info.get("date_str"))

            if fac_status in STATUS_NORMALIZE:
                fac_status = STATUS_NORMALIZE[fac_status]

            if fac_status in STATUS_ORDER:
                main_status = main_summary.get("status")
                main_date = parse_date(main_summary.get("source_date"))

                # decide override if stronger status OR newer date
                if (
                    (main_status and STATUS_RANK[fac_status] < STATUS_RANK[main_status])
                    or (pd.notna(fac_date) and pd.notna(main_date) and fac_date > main_date)
                ):
                    main_summary["status"] = fac_status
                    main_summary["overridden_by"] = "latest_factory_status"

            # remove helper field before saving
            main_summary.pop("source_date", None)

            update_fields["main"] = main_summary

        if update_fields:
            updates.append(UpdateOne({"_id": doc["_id"]}, {"$set": update_fields}))

    if updates:
        result = facilities_collection.bulk_write(updates)
        logging.info(f"✅ Updated summaries for {result.modified_count} facilities.")
    else:
        logging.info("⚠️ No facilities needed updates.")

if __name__ == "__main__":
    compute_summaries()