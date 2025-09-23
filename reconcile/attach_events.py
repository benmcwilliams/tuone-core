# attach_events.py
import sys; sys.path.append("..")
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple

import numpy as np
import pandas as pd
from pymongo import UpdateOne

from mongo_client import facilities_collection
from src.config import GROUPED_CAPACITIES, GROUPED_INVESTMENTS, ZEV_PRODUCTION
from src.capex_dictionary import CAPEX_DICT
from src.facilities_helpers import parse_capacity_value, canon_pl2
from src.attach_events_helpers import coerce_amount_eur_scalar, iso_date, norm_pl2_key, capex_lookup, event_key_capacity, event_key_investment, sort_key

logger = logging.getLogger(__name__)

STATUS_ORDER = ["operational", "under construction", "announced", "unclear"]
INVESTMENT_STATUS_ORDER = ["completed", "ongoing", "announced", "unclear"]

# -------------------- should be temporary, until we populate is_total values --------------------

def coerce_is_total(x):
    """
    Normalize is_total values.
    - Explicit False-like → False
    - Everything else (including None, NaN, blank) → True
    """
    if x is None:
        return True
    if isinstance(x, float) and np.isnan(x):
        return True
    if isinstance(x, str):
        s = x.strip().lower()
        if s in {"false", "f", "0", "no", "n", "incremental"}:
            return False
        return True
    if isinstance(x, bool):
        return x  # keep actual boolean as-is
    if isinstance(x, (int, np.integer)):
        return False if x == 0 else True
    return True

# -------------------- load & normalize --------------------

def load_capacities() -> pd.DataFrame:
    df_cap = pd.read_excel(GROUPED_CAPACITIES)
    df_zev = pd.read_excel(ZEV_PRODUCTION)
    df = pd.concat([df_cap, df_zev], ignore_index=True)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["capacity_normalized"] = df["capacity_normalized"].apply(parse_capacity_value)
    df["status"] = pd.Categorical(df["status"], categories=STATUS_ORDER, ordered=True)
    df["pl2_key"] = df["product_lv2"].apply(canon_pl2)
    df["is_total"] = df.get("is_total", pd.Series([None]*len(df))).apply(coerce_is_total)
    return df

def load_investments() -> pd.DataFrame:
    df = pd.read_excel(GROUPED_INVESTMENTS)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["status"] = pd.Categorical(df["status"], categories=INVESTMENT_STATUS_ORDER, ordered=True)
    df["pl2_key"] = df["product_lv2"].apply(canon_pl2)
    df["is_total"] = df.get("is_total", pd.Series([None]*len(df))).apply(coerce_is_total)
    return df

# -------------------- dedup & group --------------------

def dedup_group_capacities(df: pd.DataFrame) -> pd.DataFrame:
    df = (df.sort_values(["project_id", "date"], na_position="last")
            .drop_duplicates(["project_id", "capacity_normalized", "status", "phase", "pl2_key"], keep="first"))
    group_keys = ["project_id", "product_lv1", "capacity_normalized", "status", "phase"]
    g = (df.groupby(group_keys, dropna=False, sort=False, observed=True)
           .agg(pl2_union=("pl2_key", lambda T: tuple(sorted({v for tup in T for v in tup}))),
                date=("date","first"),
                articleID=("article_id","first"),
                additional=("additional","first"),
                investment=("amount_EUR","first"),
                is_total=("is_total","first"),
                investment_id=("investment_id","first"))
           .reset_index()
           .rename(columns={"pl2_union":"product_lv2"}))
    return g

def dedup_group_investments(df: pd.DataFrame) -> pd.DataFrame:
    df = (df.sort_values(["project_id", "date"], na_position="last")
            .drop_duplicates(["project_id", "amount_EUR", "status", "phase", "pl2_key"], keep="first"))
    group_keys = ["project_id", "product_lv1", "amount_EUR", "status", "phase"]
    g = (df.groupby(group_keys, dropna=False, sort=False, observed=True)
           .agg(pl2_union=("pl2_key", lambda T: tuple(sorted({v for tup in T for v in tup}))),
                date=("date","first"),
                is_total=("is_total","first"),
                articleID=("article_id","first"),
                investment_id=("investment_id","first"))
           .reset_index()
           .rename(columns={"pl2_union":"product_lv2"}))
    return g

# -------------------- build events + impute --------------------

def build_events_by_project(df_cap: pd.DataFrame, df_inv: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
    events_by_pid: Dict[str, List[Dict[str, Any]]] = {}

    # capacities
    for _, r in df_cap.iterrows():
        pid = r["project_id"]
        pl2_key = norm_pl2_key(r["product_lv2"])
        raw_amt = r.get("investment")
        amt_scalar, amt_policy = coerce_amount_eur_scalar(raw_amt)

        evt = {
            "event_type": "capacity",
            "project_id": pid,
            "product_lv1": r.get("product_lv1"),
            "product_lv2": list(pl2_key),
            "status": r.get("status"),
            "phase": r.get("phase"),
            "date": iso_date(r.get("date")),
            "articleID": r.get("articleID") if pd.notna(r.get("articleID")) else None,
            "capacityID": r.get("capacity_id"),
            "capacity": r.get("capacity_normalized"),
            "additional": bool(r.get("additional")),
            "investment": amt_scalar,
            "is_total": bool(r.get("is_total")),
            "investment_id": r.get("investment_id") if pd.notna(r.get("investment_id")) else None,
        }

        evt["event_key"] = event_key_capacity(pid, evt["product_lv1"], tuple(evt["product_lv2"]),
                                              evt["capacity"], evt["status"], evt["phase"])
        evt["eventID"] = evt["article_ID"]+"_"+evt["capacity_id"]

        # Impute missing amount from CAPEX, never overwrite direct amount
        if evt.get("investment") in (None, np.nan):
            cap_rule = capex_lookup(evt["product_lv1"], tuple(evt["product_lv2"]))
            if cap_rule and evt.get("capacity") not in (None, np.nan):
                evt["investment_imputed"] = float(evt["capacity"]) * float(cap_rule["capex_per_unit"])
                evt["imputation_basis"] = CAPEX_DICT["version"]
                evt.setdefault("data_origin", {}).setdefault("imputed", []).append("investment")
        events_by_pid.setdefault(pid, []).append(evt)

    # investments
    for _, r in df_inv.iterrows():
        pid = r["project_id"]
        pl2_key = norm_pl2_key(r["product_lv2"])
        raw_amt = r.get("investment")
        amt_scalar, amt_policy = coerce_amount_eur_scalar(raw_amt)

        evt = {
            "event_type": "investment",
            "project_id": pid,
            "product_lv1": r.get("product_lv1"),
            "product_lv2": list(pl2_key),
            "status": r.get("status"),
            "phase": r.get("phase"),
            "date": iso_date(r.get("date")),
            "articleID": [r.get("articleID")] if pd.notna(r.get("articleID")) else [],
            "investment": amt_scalar,
            "investmentID": r.get("investment_id"),
            "is_total": bool(r.get("is_total")),
            "investment_id": r.get("investment_id") if pd.notna(r.get("investment_id")) else None,
        }
        evt["event_key"] = event_key_investment(pid, evt["product_lv1"], tuple(evt["product_lv2"]),
                                                evt["investment"], evt["status"], evt["phase"], evt.get("investment_id"))
        evt["eventID"] = evt["article_ID"]+"_"+evt["investment_id"]

        # Impute missing capacity from CAPEX, never overwrite direct capacity
        if evt.get("investment") not in (None, np.nan):
            cap_rule = capex_lookup(evt["product_lv1"], tuple(evt["product_lv2"]))
            if cap_rule:
                # Only set imputed capacity if none present
                evt["capacity_imputed"] = float(evt["investment"]) / float(cap_rule["capex_per_unit"])
                evt["capacity_unit"] = cap_rule.get("capacity_unit")
                evt["imputation_basis"] = CAPEX_DICT["version"]
                evt.setdefault("data_origin", {}).setdefault("imputed", []).append("capacity")
        events_by_pid.setdefault(pid, []).append(evt)

    # Drop standalone investments overshadowed by capacity rows using same investment_id
    for pid, evts in list(events_by_pid.items()):
        cap_ids = {e.get("investment_id") for e in evts if e["event_type"] == "capacity" and e.get("investment_id")}
        if cap_ids:
            events_by_pid[pid] = [e for e in evts if not (e["event_type"] == "investment" and e.get("investment_id") in cap_ids)]

        # sort
        events_by_pid[pid].sort(key=sort_key)

    return events_by_pid

# -------------------- merge into facilities --------------------

def fetch_existing(pids: List[str]) -> Dict[str, Dict[str, Any]]:
    docs = {}
    for doc in facilities_collection.find({"project_id": {"$in": pids}}, {"_id": 0, "project_id": 1, "events": 1, "event_keys": 1}):
        docs[doc["project_id"]] = {
            "events": doc.get("events") or [],
            "event_keys": set(doc.get("event_keys") or []),
            # collect also eventIDs
        }
    return docs

def attach_events(dry_run: bool = False):

    # load
    df_cap_raw = load_capacities()
    df_inv_raw = load_investments()

    # dedup/group
    df_cap = dedup_group_capacities(df_cap_raw)
    df_inv = dedup_group_investments(df_inv_raw)
    logger.info("Capacities raw=%d → grouped=%d | Investments raw=%d → grouped=%d",
                len(df_cap_raw), len(df_cap), len(df_inv_raw), len(df_inv))

    # build
    events_by_pid = build_events_by_project(df_cap, df_inv)
    pids = list(events_by_pid.keys())
    if not pids:
        logger.warning("No events to attach.")
        return

    # fetch existing facilities/events
    existing = fetch_existing(pids)
    updates: List[UpdateOne] = []
    missing = 0

    for pid in pids:
        if pid not in existing:
            print(pid)
            missing += 1
            continue

        incoming_events = events_by_pid[pid]
        incoming_keys = sorted({e.get("event_key") for e in incoming_events if e.get("event_key")})

        # always overwrite with incoming events
        updates.append(UpdateOne({"project_id": pid}, {"$set": {
            "events": incoming_events,
            "event_keys": incoming_keys,
            "last_updated_at": datetime.utcnow(),
        }}))

    logger.info("attach_events → facilities matched: %d | missing: %d | to update: %d",
                len(existing), missing, len(updates))

    if dry_run or not updates:
        if dry_run:
            logger.info("Dry-run enabled: no DB writes.")
        return

    facilities_collection.bulk_write(updates, ordered=False)
    logger.info("✅ attach_events: updated %d facilities.", len(updates))

if __name__ == "__main__":
    attach_events()