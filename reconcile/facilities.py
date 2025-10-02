# facilities.py
# -----------------------------------------------------------------------------
# PURPOSE
#   Write facilities from excel to mongoDB. Add any new, delete stale & update latest_facility_status
# -----------------------------------------------------------------------------

import sys; sys.path.append("..")
import logging
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from pymongo import UpdateOne
from src.facilities_helpers import _normalize_pl2, _agg_norm_list, _as_dt
from mongo_client import facilities_collection, test_mongo_connection
from src.config import GROUPED_FACTORIES

def _latest_status_per_project(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return (
        df.loc[df["factory_status"].notna(), ["project_id", "factory_status", "date"]]
          .sort_values(["project_id", "date"])
          .groupby("project_id", as_index=False)
          .tail(1)
          .rename(columns={"date": "factory_status_date"})
    )

def _build_facilities_df() -> pd.DataFrame:
    df = pd.read_excel(GROUPED_FACTORIES)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    latest = _latest_status_per_project(df)
    return (
        df.groupby("project_id", as_index=False)
          .agg({
              "inst_canon": "first",
              "iso2": "first",
              "adm1": "first",
              "admin_group_key": "first",
              "lat": "first",
              "lon": "first",
              "product_lv1": "first",
              #"product_lv2": _agg_norm_list, 
              "product": _agg_norm_list,        
          })
          .merge(latest, on="project_id", how="left")
    )

def _to_doc(row: pd.Series) -> Dict[str, Any]:
    return {
        "project_id": row["project_id"],
        "inst_canon": row.get("inst_canon") if pd.notna(row.get("inst_canon")) else None,
        "iso2": row.get("iso2") if pd.notna(row.get("iso2")) else None,
        "adm1": row.get("adm1") if pd.notna(row.get("adm1")) else None,
        "admin_group_key": row.get("admin_group_key") if pd.notna(row.get("admin_group_key")) else None,
        "lat": row.get("lat") if pd.notna(row.get("lat")) else None,
        "lon": row.get("lon") if pd.notna(row.get("lon")) else None,
        "product_lv1": row.get("product_lv1") if pd.notna(row.get("product_lv1")) else None,
        #"product_lv2": _normalize_pl2(row.get("product_lv2")),   # << canonicalized write
        #"products":    _normalize_pl2(row.get("product")),
        "latest_factory_status": {
            "status": row.get("factory_status") if pd.notna(row.get("factory_status")) else None,
            "date": (pd.to_datetime(row.get("factory_status_date"))
                        .to_pydatetime().replace(tzinfo=None)
                        if pd.notna(row.get("factory_status_date")) else None),
        }
    }

def _compute_update(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    update: Dict[str, Any] = {}

    # UPDATE | latest_factory_status comparison on full datetime + status text
    old_s = existing.get("latest_factory_status") or {}
    new_s = incoming.get("latest_factory_status") or {}

    old_dt = _as_dt(old_s.get("date"))
    new_dt = _as_dt(new_s.get("date"))

    old_status = (old_s.get("status") or None)
    new_status = (new_s.get("status") or None)

    should_update_status = False
    if new_s:
        if old_dt is None and new_dt is not None:
            should_update_status = True
        elif old_dt is not None and new_dt is not None:
            should_update_status = (new_dt > old_dt) or (new_dt == old_dt and new_status != old_status)
        elif old_dt is None and new_dt is None:
            should_update_status = (new_status != old_status)

    if should_update_status:
        update["latest_factory_status"] = new_s

    if update:
        update["last_updated_at"] = datetime.utcnow()
        return {"$set": update}
    return {}

def upsert_facilities(docs: List[Dict[str, Any]], dry_run: bool = False, prune_missing: bool = True) -> None:
    # Fetch existing docs for the candidate project_ids
    pids = [d["project_id"] for d in docs]
    existing = {
        d["project_id"]: d
        for d in facilities_collection.find({"project_id": {"$in": pids}}, {"_id": 0})
    }

    inserts, updates = [], []
    for doc in docs:
        pid = doc["project_id"]
        if pid not in existing:
            inserts.append(doc)
        else:
            upd = _compute_update(existing[pid], doc)
            if upd:
                updates.append(UpdateOne({"project_id": pid}, upd))
                logging.info("Update %s: %s", existing.get("project_id"), list(upd["$set"].keys()))

    # --- NEW: prune facilities whose project_id is NOT in the incoming list ---
    stale_ids = []
    if prune_missing:
        incoming_set = set(pids)
        # get ALL existing project_ids (not only the ones we fetched above)
        existing_all = set(facilities_collection.distinct("project_id"))
        stale_ids = list(existing_all - incoming_set)

    logging.info("Facilities → inserts: %d | updates: %d | total input: %d", len(inserts), len(updates), len(docs))
    if prune_missing:
        logging.info("Facilities → stale (to remove): %d", len(stale_ids))

    if dry_run:
        logging.info("Dry-run: no DB writes.")
        return

    if inserts:
        facilities_collection.insert_many(inserts, ordered=False)
    if updates:
        facilities_collection.bulk_write(updates, ordered=False)

    # we should incorporate the shift to is_active: False, and deleted_at (but need to update whole pipeline)
    if prune_missing and stale_ids:
        # HARD DELETE (use with care). Comment this block if you prefer soft delete.
        facilities_collection.delete_many({"project_id": {"$in": stale_ids}})
        # SOFT DELETE alternative:
        # facilities_collection.update_many(
        #     {"project_id": {"$in": stale_ids}},
        #     {"$set": {"is_active": False, "deleted_at": datetime.utcnow()}}
        # )

def write_facilities():
    test_mongo_connection()
    df_fac = _build_facilities_df()
    docs = [_to_doc(r) for _, r in df_fac.iterrows()]
    upsert_facilities(docs, dry_run=False, prune_missing=True)

if __name__ == "__main__":
    # One-time setup (outside this script): facilities_collection.create_index("project_id", unique=True)
    write_facilities()