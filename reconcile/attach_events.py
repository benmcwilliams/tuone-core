# attach_events.py
import sys; sys.path.append("..")
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple

import numpy as np
import pandas as pd
from pymongo import UpdateOne

from mongo_client import facilities_collection, test_mongo_connection
from src.config import GROUPED_CAPACITIES, GROUPED_INVESTMENTS, ZEV_PRODUCTION
from src.capex_dictionary import CAPEX_DICT
from src.facilities_helpers import parse_capacity_value, canon_pl2
#from src.article_validation import build_article_validation_map, compute_validated_flag  can drop this if Ross calculates directly from mongoDB.
from src.attach_events_helpers import coerce_amount_eur_scalar

logger = logging.getLogger(__name__)

STATUS_ORDER = ["operational", "under construction", "announced", "unclear"]
INVESTMENT_STATUS_ORDER = ["completed", "ongoing", "announced", "unclear"]

# -------------------- helpers --------------------

def iso_date(dt) -> str | None:
    if pd.isna(dt): return None
    if isinstance(dt, str): return dt
    d = pd.to_datetime(dt, errors="coerce")
    return d.strftime("%Y-%m-%d") if pd.notna(d) else None

def norm_pl2_key(values) -> Tuple[str, ...]:
    vals = [v for v in (values or []) if pd.notna(v)]
    return tuple(sorted({str(v).strip() for v in vals}))

def capex_lookup(product_lv1: str, pl2_key: Tuple[str, ...]) -> Dict[str, Any] | None:
    """Exact match on (product_lv1, product_lv2_key). Units are assumed normalized upstream."""
    for e in CAPEX_DICT.get("entries", []):
        if e.get("product_lv1") == product_lv1 and tuple(e.get("product_lv2_key") if isinstance(e.get("product_lv2_key"), (list, tuple)) else (e.get("product_lv2_key"),)) == pl2_key:
            return e
    return None

def event_key_capacity(project_id, product_lv1, pl2_key, capacity_normalized, status, phase) -> str:
    return "|".join(map(str, ("capacity", project_id, product_lv1, pl2_key, capacity_normalized, status, phase)))

def event_key_investment(project_id, product_lv1, pl2_key, amount_EUR, status, phase, investment_id=None) -> str:
    if investment_id:  # prefer natural ID
        return "|".join(map(str, ("investment_id", project_id, investment_id)))
    return "|".join(map(str, ("investment", project_id, product_lv1, pl2_key, amount_EUR, status, phase)))

def sort_key(e: Dict[str, Any]):
    d = iso_date(e.get("date"))
    return (d or "9999-12-31", 0 if e.get("event_type") == "investment" else 1)

# -------------------- load & normalize --------------------

def load_capacities() -> pd.DataFrame:
    df_cap = pd.read_excel(GROUPED_CAPACITIES)
    df_zev = pd.read_excel(ZEV_PRODUCTION)
    df = pd.concat([df_cap, df_zev], ignore_index=True)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["capacity_normalized"] = df["capacity_normalized"].apply(parse_capacity_value)
    df["status"] = pd.Categorical(df["status"], categories=STATUS_ORDER, ordered=True)
    df["pl2_key"] = df["product_lv2"].apply(canon_pl2)
    return df

def load_investments() -> pd.DataFrame:
    df = pd.read_excel(GROUPED_INVESTMENTS)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["status"] = pd.Categorical(df["status"], categories=INVESTMENT_STATUS_ORDER, ordered=True)
    df["pl2_key"] = df["product_lv2"].apply(canon_pl2)
    return df

# -------------------- dedup & group --------------------

def dedup_group_capacities(df: pd.DataFrame) -> pd.DataFrame:
    df = (df.sort_values(["project_id", "date"], na_position="last")
            .drop_duplicates(["project_id", "capacity_normalized", "status", "phase", "pl2_key"], keep="first"))
    group_keys = ["project_id", "product_lv1", "capacity_normalized", "status", "phase"]
    g = (df.groupby(group_keys, dropna=False, sort=False, observed=True)
           .agg(pl2_union=("pl2_key", lambda T: tuple(sorted({v for tup in T for v in tup}))),
                date=("date","first"),
                article_id=("article_id","first"),
                amount_EUR=("amount_EUR","first"),
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
                article_id=("article_id","first"),
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
        raw_amt = r.get("amount_EUR")
        amt_scalar, amt_policy = coerce_amount_eur_scalar(raw_amt)

        evt = {
            "event_type": "capacity",
            "project_id": pid,
            "product_lv1": r.get("product_lv1"),
            "product_lv2": list(pl2_key),
            "status": r.get("status"),
            "phase": r.get("phase"),
            "date": iso_date(r.get("date")),
            "article_id": r.get("article_id") if pd.notna(r.get("article_id")) else None,
            "capacity_normalized": r.get("capacity_normalized"),
            "amount_EUR": amt_scalar,
            "investment_id": r.get("investment_id") if pd.notna(r.get("investment_id")) else None,
        }

        evt["event_key"] = event_key_capacity(pid, evt["product_lv1"], tuple(evt["product_lv2"]),
                                              evt["capacity_normalized"], evt["status"], evt["phase"])

        # Impute missing amount from CAPEX, never overwrite direct amount
        if evt.get("amount_EUR") in (None, np.nan):
            cap_rule = capex_lookup(evt["product_lv1"], tuple(evt["product_lv2"]))
            if cap_rule and evt.get("capacity_normalized") not in (None, np.nan):
                evt["amount_EUR_imputed"] = float(evt["capacity_normalized"]) * float(cap_rule["capex_per_unit"])
                evt["imputation_basis"] = CAPEX_DICT["version"]
                evt.setdefault("data_origin", {}).setdefault("imputed", []).append("amount_EUR")
        events_by_pid.setdefault(pid, []).append(evt)

    # investments
    for _, r in df_inv.iterrows():
        pid = r["project_id"]
        pl2_key = norm_pl2_key(r["product_lv2"])
        raw_amt = r.get("amount_EUR")
        amt_scalar, amt_policy = coerce_amount_eur_scalar(raw_amt)

        evt = {
            "event_type": "investment",
            "project_id": pid,
            "product_lv1": r.get("product_lv1"),
            "product_lv2": list(pl2_key),
            "status": r.get("status"),
            "phase": r.get("phase"),
            "date": iso_date(r.get("date")),
            "article_id": [r.get("article_id")] if pd.notna(r.get("article_id")) else [],
            "amount_EUR": amt_scalar,
            "investment_id": r.get("investment_id") if pd.notna(r.get("investment_id")) else None,
        }
        evt["event_key"] = event_key_investment(pid, evt["product_lv1"], tuple(evt["product_lv2"]),
                                                evt["amount_EUR"], evt["status"], evt["phase"], evt.get("investment_id"))
        # Impute missing capacity from CAPEX, never overwrite direct capacity
        if evt.get("amount_EUR") not in (None, np.nan):
            cap_rule = capex_lookup(evt["product_lv1"], tuple(evt["product_lv2"]))
            if cap_rule:
                # Only set imputed capacity if none present
                evt["capacity_imputed"] = float(evt["amount_EUR"]) / float(cap_rule["capex_per_unit"])
                evt["capacity_unit"] = cap_rule.get("capacity_unit")
                evt["imputation_basis"] = CAPEX_DICT["version"]
                evt.setdefault("data_origin", {}).setdefault("imputed", []).append("capacity_normalized")
        events_by_pid.setdefault(pid, []).append(evt)

    # Drop standalone investments overshadowed by capacity rows using same investment_id
    for pid, evts in list(events_by_pid.items()):
        cap_ids = {e.get("investment_id") for e in evts if e["event_type"] == "capacity" and e.get("investment_id")}
        if cap_ids:
            events_by_pid[pid] = [e for e in evts if not (e["event_type"] == "investment" and e.get("investment_id") in cap_ids)]

        # sort
        events_by_pid[pid].sort(key=sort_key)

        # annotate first_seen / last_seen defaults
        for e in events_by_pid[pid]:
            d = e.get("date")
            e["first_seen_date"] = d
            e["last_seen_date"] = d

    return events_by_pid

# -------------------- merge into facilities --------------------

def fetch_existing(pids: List[str]) -> Dict[str, Dict[str, Any]]:
    docs = {}
    for doc in facilities_collection.find({"project_id": {"$in": pids}}, {"_id": 0, "project_id": 1, "events": 1, "event_keys": 1}):
        docs[doc["project_id"]] = {
            "events": doc.get("events") or [],
            "event_keys": set(doc.get("event_keys") or []),
        }
    return docs

def merge_events(existing: Dict[str, Any], incoming: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    by_key = {e.get("event_key"): e for e in existing["events"] if e.get("event_key")}
    keys = set(existing["event_keys"])

    for e in incoming:
        k = e.get("event_key")
        if not k: 
            continue
        if k in by_key:
            cur = by_key[k]

            # keep the original article_id if present; otherwise adopt incoming
            if not cur.get("article_id") and e.get("article_id"):
                cur["article_id"] = e["article_id"]

            # update first/last seen
            d = e.get("date")
            if d:
                cur["first_seen_date"] = min(filter(None, [cur.get("first_seen_date"), d]))
                cur["last_seen_date"]  = max(filter(None, [cur.get("last_seen_date"), d]))
            # add imputed fields ONLY if missing direct counterparts
            if "amount_EUR_imputed" in e and cur.get("amount_EUR") in (None, np.nan):
                cur["amount_EUR_imputed"] = e["amount_EUR_imputed"]
                cur["imputation_basis"] = e.get("imputation_basis", cur.get("imputation_basis"))
                cur.setdefault("data_origin", {}).setdefault("imputed", []).append("amount_EUR")
            if "capacity_imputed" in e and cur.get("capacity_normalized") in (None, np.nan):
                cur["capacity_imputed"] = e["capacity_imputed"]
                cur["capacity_unit"] = e.get("capacity_unit", cur.get("capacity_unit"))
                cur["imputation_basis"] = e.get("imputation_basis", cur.get("imputation_basis"))
                cur.setdefault("data_origin", {}).setdefault("imputed", []).append("capacity_normalized")
        else:
            by_key[k] = e
            keys.add(k)

    merged = list(by_key.values())
    merged.sort(key=sort_key)
    return merged, sorted(list(keys))

def attach_events(dry_run: bool = False):
    test_mongo_connection()

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
        merged_events, merged_keys = merge_events(existing[pid], events_by_pid[pid])
        # only write if changed
        if (len(merged_events) != len(existing[pid]["events"])) or (set(merged_keys) != existing[pid]["event_keys"]):
            updates.append(UpdateOne({"project_id": pid}, {"$set": {
                "events": merged_events,
                "event_keys": merged_keys,
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