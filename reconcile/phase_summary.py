import logging
import sys; sys.path.append("..")
from pymongo import UpdateOne
from datetime import datetime
import pandas as pd  # for robust datetime handling
from mongo_client import facilities_collection, test_mongo_connection

# Strongest first
STATUS_ORDER = ["cancelled", "paused", "operational", "under construction", "announced", "unclear"]
STATUS_RANK = {status: i for i, status in enumerate(STATUS_ORDER)}

def parse_date(date_str):
    try:
        return pd.to_datetime(date_str)
    except Exception:
        return pd.NaT

def build_phase_summary(capacities: list, phase: str | None) -> dict | None:
    # filter for relevant phase or output "main" with None
    phase_caps = [
        c for c in capacities
        if (phase is None or c.get("phase") == phase)
        and c.get("status") in STATUS_ORDER
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

    summary = {
        "status": best["status"],
        "capacity": best["amount"],
        "source_date": best["date"],
    }

    # add chronological milestone dates (we take the earliest date each milestone is mentioned)
    for milestone in ["announced", "under construction", "operational"]:
        first = next(
            (c for c in sorted(phase_caps, key=lambda c: parse_date(c["date"]))
             if c["status"] == milestone),
            None
        )
        if first:
            summary[f"{milestone.replace(' ', '_')}_on"] = first["date"]

    return summary

def determine_phase_summary():
    test_mongo_connection()
    logging.info("🚀 Starting summary updates for main, greenfield and expansion...")

    updates = []

    for doc in facilities_collection.find({}):
        capacities = doc.get("capacities", [])
        
        # current logic to override status with facility level status if later 
        latest_fac = doc.get("latest_factory_status") or {}
        latest_fac_date = parse_date(latest_fac.get("date") or latest_fac.get("date_str"))
        latest_fac_status = latest_fac.get("status")

        update_fields = {}
        # write summaries for greenfield, expansion and main
        for out_key, phase in [("greenfield", "greenfield"),
                               ("expansion", "expansion"),
                               ("main", None)]:
            summary = build_phase_summary(capacities, phase)
            if not summary:
                continue

            # final check: if facility status is NEWER than the deciding capacity date, override
            cap_deciding_date = parse_date(summary.get("source_date"))
            if pd.notna(latest_fac_date) and pd.notna(cap_deciding_date) and latest_fac_date > cap_deciding_date and latest_fac_status:
                summary["status"] = latest_fac_status
                summary["overridden_by"] = "latest_factory_status"  # optional breadcrumb

            summary.pop("source_date", None)  # don’t store the internal helper field
            update_fields[out_key] = summary

        if update_fields:
            updates.append(UpdateOne({"_id": doc["_id"]}, {"$set": update_fields}))

    if updates:
        result = facilities_collection.bulk_write(updates)
        logging.info(f"✅ Updated summaries for {result.modified_count} facilities.")
    else:
        logging.info("⚠️ No facilities needed updates.")

if __name__ == "__main__":
    determine_phase_summary()