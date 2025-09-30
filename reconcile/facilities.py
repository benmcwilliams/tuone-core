import sys; sys.path.append("..")
import logging
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from pymongo import UpdateOne
from mongo_client import facilities_collection, test_mongo_connection
from src.config import GROUPED_FACTORIES

def _latest_status_per_project(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m", errors="coerce")
    return (
        df.loc[df["factory_status"].notna(), ["project_id", "factory_status", "date"]]
          .sort_values(["project_id", "date"])
          .groupby("project_id", as_index=False)
          .tail(1)
          .rename(columns={"date": "factory_status_date"})
    )

def _build_facilities_df() -> pd.DataFrame:
    df = pd.read_excel(GROUPED_FACTORIES)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m", errors="coerce")
    latest = _latest_status_per_project(df)
    return (
        df.groupby("project_id", as_index=False)
          .agg({
              "inst_canon": "first",
              "iso2": "first",
              "adm1": "first",
              "lat": "first",
              "lon": "first",
              "product_lv1": "first",
              "product_lv2": lambda s: [v for v in np.unique([x for x in s if pd.notna(x)])],
              "product": lambda s: [v for v in np.unique([x for x in s if pd.notna(x)])]
          })
          .merge(latest, on="project_id", how="left")
    )

def _iso_date(dt) -> str | None:
    if pd.isna(dt): return None
    if isinstance(dt, str): return dt
    return pd.to_datetime(dt, errors="coerce").strftime("%Y-%m-%d") if pd.notna(dt) else None

def _to_doc(row: pd.Series) -> Dict[str, Any]:
    return {
        "project_id": row["project_id"],
        "inst_canon": row.get("inst_canon") if pd.notna(row.get("inst_canon")) else None,
        "iso2": row.get("iso2") if pd.notna(row.get("iso2")) else None,
        "adm1": row.get("adm1") if pd.notna(row.get("adm1")) else None,
        "lat": row.get("lat") if pd.notna(row.get("lat")) else None,
        "lon": row.get("lon") if pd.notna(row.get("lon")) else None,
        "product_lv1": row.get("product_lv1") if pd.notna(row.get("product_lv1")) else None,
        "product_lv2": [v for v in (row.get("product_lv2") or []) if pd.notna(v)],
        "products": [v for v in (row.get("product") or []) if pd.notna(v)],
        "latest_factory_status": {
            "status": row.get("factory_status") if pd.notna(row.get("factory_status")) else None,
            "date": _iso_date(row.get("factory_status_date")),
        }
    }

def _normalize_pl2(vals) -> List[str]:
    return sorted({str(v).strip() for v in (vals or []) if pd.notna(v)})

def _parse_dt(s: str | None):
    return pd.to_datetime(s, errors="coerce") if s else pd.NaT

def _compute_update(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    update: Dict[str, Any] = {}

    # product_lv2: union | overwrite product_lv2 value if difference
    old_pl2 = _normalize_pl2(existing.get("product_lv2"))
    new_pl2 = _normalize_pl2(incoming.get("product_lv2"))
    if new_pl2 != old_pl2:
        update["product_lv2"] = new_pl2

    # latest_factory_status: update if newer or text changed
    old_s = existing.get("latest_factory_status") or {}
    new_s = incoming.get("latest_factory_status") or {}
    old_dt, new_dt = _parse_dt(old_s.get("date")), _parse_dt(new_s.get("date"))
    should_update_status = False
    if new_s:
        if pd.isna(old_dt) and not pd.isna(new_dt):
            should_update_status = True
        elif not pd.isna(old_dt) and not pd.isna(new_dt):
            should_update_status = (new_dt > old_dt) or (new_dt == old_dt and old_s.get("status") != new_s.get("status"))
        elif pd.isna(old_dt) and pd.isna(new_dt):
            should_update_status = (old_s.get("status") != new_s.get("status"))
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