# attach_events.py
# -----------------------------------------------------------------------------
# PURPOSE
#   Attach capacity and investment events to facilities in MongoDB.
#   Deduplicate and group events by project_id, article_id, product_lv1, product_lv2, status, phase.
#   Build events object from excel and merge into facilities.
#   Impute missing amounts from CAPEX.
#   Sort events by date and eventID.
#   Overlay user-edited phase_num from existing by eventID.
#   Write events to facilities.
# -----------------------------------------------------------------------------

import sys; sys.path.append("..")
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple

import numpy as np
import pandas as pd
from pymongo import UpdateOne

from mongo_client import facilities_collection
from src.config import GROUPED_CAPACITIES, GROUPED_INVESTMENTS, ZEV_PRODUCTION, GROUPED_FACTORIES
from src.capex_dictionary import CAPEX_DICT
from src.facilities_helpers import parse_capacity_value
from src.attach_events_helpers import coerce_amount_scalar, iso_date, normalize_pl2, capex_lookup, sort_key, _unit_capex, coerce_is_total, union_pl2_lists

logger = logging.getLogger(__name__)

STATUS_ORDER = ["cancelled", "paused", "operational", "under construction", "announced", "unclear"]
INVESTMENT_STATUS_ORDER = ["cancelled", "paused", "completed", "ongoing", "announced", "unclear"]

INCLUDE_FACTORY_EVENTS = True
AMOUNT_COL = "amount_EUR_2023_ameco_pvgd"
# "amount_EUR_2023_ameco_pvgd"

# -------------------- load & normalize --------------------

def load_capacities() -> pd.DataFrame:
    """
    Load capacity fragments & EV Volumes productions
    """
    df_cap = pd.read_excel(GROUPED_CAPACITIES)
    df_zev = pd.read_excel(ZEV_PRODUCTION)
    df = pd.concat([df_cap, df_zev], ignore_index=True)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["capacity_normalized"] = df["capacity_normalized"].apply(parse_capacity_value)
    df["status"] = pd.Categorical(df["status"], categories=STATUS_ORDER, ordered=True)
    df["prod_key"] = df["product"].apply(lambda x: tuple(normalize_pl2(x, lowercase=True)))
    return df

def load_investments() -> pd.DataFrame:
    df = pd.read_excel(GROUPED_INVESTMENTS)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["status"] = pd.Categorical(df["status"], categories=INVESTMENT_STATUS_ORDER, ordered=True)
    df["prod_key"] = df["product"].apply(lambda x: tuple(normalize_pl2(x, lowercase=True)))
    return df

def load_factories() -> pd.DataFrame: 
    """
    Lightweight load of factory-level rows used to create 'facility' events.
    Expects columns: project_id, product_lv1, product_lv2, factory_status, date, article_id
    """
    df = pd.read_excel(GROUPED_FACTORIES)
    df = df.rename(columns={"factory_status": "status"})
    df["date"] = pd.to_datetime(df.get("date"), errors="coerce")
    df["status"] = pd.Categorical(df.get("status"), categories=STATUS_ORDER, ordered=True)
    df["prod_key"] = df.get("product").apply(lambda x: tuple(normalize_pl2(x, lowercase=True)))
    return df

# -------------------- dedup & group --------------------

def dedup_group_capacities(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate factory rows conservatively to avoid repetitive investment events.
    Keep distinct by (project_id, article_id, product_lv1, product_lv2, capacity, status, phase)
    """
    df = (df.sort_values(["project_id", "date"], ascending=[True, False], na_position="last"))
    group_keys = ["project_id", "article_id", "product_lv1", "product_lv2", "capacity_normalized", "status", "phase"]
    g = (df.groupby(group_keys, dropna=False, sort=False, observed=True)
           .agg(prod_union=("prod_key", union_pl2_lists),
                date=("date","first"),
                additional=("additional","first"),
                amount=(AMOUNT_COL,"first"),
                is_total=("is_total","first"),
                capacity_id=("capacity_id","first"),
                investment_id=("investment_id","first"))
           .reset_index())
    return g

def dedup_group_investments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate factory rows conservatively to avoid repetitive investment events.
    Keep distinct by (project_id, article_id, product_lv1, product_lv2, AMOUNT_COL, status, phase)
    """
    df = (df.sort_values(["project_id", "date"], ascending=[True, False], na_position="last"))
    group_keys = ["project_id", "article_id", "product_lv1", "product_lv2", AMOUNT_COL, "status", "phase"]
    g = (df.groupby(group_keys, dropna=False, sort=False, observed=True)
           .agg(prod_union=("prod_key", union_pl2_lists),
                date=("date","first"),
                amount=(AMOUNT_COL,"first"),
                is_total=("is_total","first"),
                investment_id=("investment_id","first"))
           .reset_index())
    return g

def dedup_group_factories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate factory rows conservatively to avoid repetitive facility events.
    Keep distinct by (project_id, article_id, product_lv1, product_lv2, status)
    """
    df = (df.sort_values(["project_id", "date"], ascending=[True, False], na_position="last"))
    group_keys = ["project_id", "article_id", "product_lv1", "product_lv2", "status"]
    g = (df.groupby(group_keys, dropna=False, sort=False, observed=True)
           .agg(prod_union=("prod_key", union_pl2_lists),
                date=("date", "first"))
           .reset_index())
    return g

# -------------------- build events + impute --------------------

def build_events_by_project(df_cap: pd.DataFrame, df_inv: pd.DataFrame, df_fac: pd.DataFrame | None = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Build an events object from the incoming excel ready to attach to mongoDB facilities.
    """
    events_by_pid: Dict[str, List[Dict[str, Any]]] = {}

    # capacities
    for _, r in df_cap.iterrows():
        pid = r["project_id"]
        raw_amt = r.get("amount")
        amt_scalar, amt_policy = coerce_amount_scalar(raw_amt)
        products = normalize_pl2(r["prod_union"])

        evt = {
            "event_type": "capacity",
            "project_id": pid,
            "product_lv1": r.get("product_lv1"),
            "product_lv2": r.get("product_lv2"),
            "products": products,
            "status": r.get("status"),
            "phase": r.get("phase"),
            "date": iso_date(r.get("date")),
            "articleID": r.get("article_id") if pd.notna(r.get("article_id")) else None,
            "capacity_id": r.get("capacity_id"),
            "capacity": r.get("capacity_normalized"),
            "additional": bool(r.get("additional")) if pd.notna(r.get("additional")) else False,
            "investment": amt_scalar,
            "is_total": coerce_is_total(r.get("is_total")),
            "investment_id": r.get("investment_id") if pd.notna(r.get("investment_id")) else None,
        }
        
        evt["eventID"] = evt["capacity_id"]

        # Impute missing amount from CAPEX, never overwrite direct amount
        if evt.get("investment") in (None, np.nan):
            cap_rule = capex_lookup(evt["product_lv1"], tuple(normalize_pl2(evt["product_lv2"])))
            if cap_rule and evt.get("capacity") not in (None, np.nan):
                unit = _unit_capex(cap_rule, evt.get("phase"))
                evt["investment_imputed"] = float(evt["capacity"]) * unit
                evt["imputation_basis"] = CAPEX_DICT["version"]
                if (evt.get("phase") or "").strip().lower() == "retrofit":
                    evt["imputation_variant"] = "retrofit"
                evt.setdefault("data_origin", {}).setdefault("imputed", []).append("investment")
        events_by_pid.setdefault(pid, []).append(evt)

    # investments
    for _, r in df_inv.iterrows():
        pid = r["project_id"]
        raw_amt = r.get("amount")
        amt_scalar, amt_policy = coerce_amount_scalar(raw_amt)
        products = normalize_pl2(r["prod_union"])

        evt = {
            "event_type": "investment",
            "project_id": pid,
            "product_lv1": r.get("product_lv1"),
            "product_lv2": r.get("product_lv2"),
            "products": products,
            "status": r.get("status"),
            "phase": r.get("phase"),
            "date": iso_date(r.get("date")),
            "articleID": r.get("article_id") if pd.notna(r.get("article_id")) else None,
            "investment": amt_scalar,
            "is_total": coerce_is_total(r.get("is_total")),
            "investment_id": r.get("investment_id") if pd.notna(r.get("investment_id")) else None,
        }

        evt["eventID"] = evt["investment_id"]

        # Impute missing capacity from CAPEX, never overwrite direct capacity
        if evt.get("investment") not in (None, np.nan):
            cap_rule = capex_lookup(evt["product_lv1"], tuple(normalize_pl2(evt["product_lv2"])))
            if cap_rule:
                unit = _unit_capex(cap_rule, evt.get("phase"))
                if unit:  # avoid divide-by-zero
                    evt["capacity_imputed"] = float(evt["investment"]) / unit
                    evt["capacity_unit"] = cap_rule.get("capacity_unit")
                    evt["imputation_basis"] = CAPEX_DICT["version"]
                    if (evt.get("phase") or "").strip().lower() == "retrofit":
                        evt["imputation_variant"] = "retrofit"
                    evt.setdefault("data_origin", {}).setdefault("imputed", []).append("capacity")
        events_by_pid.setdefault(pid, []).append(evt)
        
    # logic to include FACTORY_ONLY events (important for status & product_lv2 mapping)
    if INCLUDE_FACTORY_EVENTS and df_fac is not None and not df_fac.empty:  # NEW
        # Pre-index factory rows per project for a single pass
        fac_by_pid: Dict[str, List[Dict[str, Any]]] = {}
        for _, r in df_fac.iterrows():
            pid = r["project_id"]
            fac_by_pid.setdefault(pid, []).append(r)

        for pid, rows in fac_by_pid.items():
            existing = events_by_pid.setdefault(pid, [])
            # Build a set of articleIDs already present in capacity/investment events
            seen_article_ids = {
                e.get("articleID")
                for e in existing
                if e.get("articleID")
            }

            for r in rows:
                art_id = r.get("article_id")
                if pd.isna(art_id) or art_id is None:
                    continue  # cannot dedup without article
                if art_id in seen_article_ids:
                    continue  # skip duplicate based on articleID

                products = normalize_pl2(r["prod_union"])

                evt = {
                    "event_type": "facility",
                    "eventID": art_id,
                    "project_id": pid, 
                    "product_lv1": r.get("product_lv1"),
                    "product_lv2": r.get("product_lv2"),
                    "products": products,
                    "status": r.get("status"),
                    "phase": None,
                    "date": iso_date(r.get("date")),
                    "articleID": art_id,
                }
                existing.append(evt)
                seen_article_ids.add(art_id)  # maintain set as we add

    # sort (now includes facility events)
    for pid in list(events_by_pid.keys()):
        events_by_pid[pid].sort(key=sort_key)

    return events_by_pid

# -------------------- merge into facilities --------------------

def fetch_existing(pids: List[str]) -> Dict[str, Dict[str, Any]]:
    docs = {}
    for doc in facilities_collection.find(
        {"project_id": {"$in": pids}},
        {"_id": 0, "project_id": 1, "events": 1} 
    ):
        docs[doc["project_id"]] = {
            "events": doc.get("events") or [],
        }
    return docs

def attach_events(dry_run: bool = False):

    # load
    df_cap_raw = load_capacities()
    df_inv_raw = load_investments()
    df_fac_raw = load_factories() if INCLUDE_FACTORY_EVENTS else pd.DataFrame()

    # dedup/group
    df_cap = dedup_group_capacities(df_cap_raw)
    df_inv = dedup_group_investments(df_inv_raw)
    df_fac = dedup_group_factories(df_fac_raw) if INCLUDE_FACTORY_EVENTS and not df_fac_raw.empty else pd.DataFrame()

    logger.info("Capacities raw=%d → grouped=%d | Investments raw=%d → grouped=%d",
                len(df_cap_raw), len(df_cap), len(df_inv_raw), len(df_inv))

    # build events from excel
    events_by_pid = build_events_by_project(df_cap, df_inv, df_fac)
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

        # Overlay user-edited phase_num from existing by eventID
        prior = existing[pid]["events"]
        phase_overrides = {
            e.get("eventID"): e.get("phase_num")
            for e in prior
            if e.get("eventID") and (e.get("phase_num") is not None)
        }
        for e in incoming_events:
            eid = e.get("eventID")
            if eid in phase_overrides:
                e["phase_num"] = phase_overrides[eid]
                e["phase_num_source"] = "user"

        # Write only incoming (drops stale)
        updates.append(UpdateOne(
            {"project_id": pid},
            {"$set": {
                "events": incoming_events,
                "last_updated_at": datetime.utcnow(),
            }}
        ))

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