import numpy as np
import pandas as pd
import ast
from typing import List

def _normalize_pl2(vals) -> List[str]:
    return sorted({str(v).strip() for v in (vals or []) if pd.notna(v)})

def _agg_norm_list(s: pd.Series) -> list[str]:
    return sorted({str(x).strip() for x in s if pd.notna(x) and str(x).strip()})

# logic to compare dates
def _as_dt(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    # Mongo returns Python datetime; pandas gives Timestamp. Normalize both.
    ts = pd.to_datetime(x, errors="coerce", utc=False)
    if pd.isna(ts):
        return None
    # ensure naive (UTC assumed) for stable BSON writes/reads
    if getattr(ts, "tzinfo", None) is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts.to_pydatetime()

# parse capacity value
def parse_capacity_value(val):
    try:
        if isinstance(val, str) and val.startswith('[') and val.endswith(']'):
            numbers = ast.literal_eval(val)
            if isinstance(numbers, list) and len(numbers) == 2:
                return sum(numbers) / 2
            else:
                return np.nan
        return float(val)
    except:
        return np.nan

# normalize/hash product_lv2 for use as a dedup key 
def canon_pl2(x):
    vals = [
        str(v).strip().lower()
        for v in np.atleast_1d(x)
        if pd.notna(v)
    ]
    if not vals:
        return tuple()              # empty tuple as canonical "no products"
    return tuple(sorted(set(vals))) # sorted unique, hashable

def classify_pl2_applies_to(pl2_values):
    s = {str(v).strip().lower() for v in pl2_values if pd.notna(v)}
    has_e = "electric" in s
    has_f = "fossil" in s
    if has_e and not has_f: return "electric"
    if has_f and not has_e: return "fossil"
    return "mix"

def row_to_capacity(r):
    pl2 = list(r["product_lv2"])
    return {
        "event_type": "capacity",
        "amount": r["capacity_normalized"],
        "investment": r.get("amount_EUR"),
        "investment_id": r.get("investment_id"),
        "status": r["status"] if pd.notna(r["status"]) else None,
        "phase":  r["phase"] if pd.notna(r["phase"]) else None,
        "product_lv2": pl2,
        "applies_to": classify_pl2_applies_to(pl2),
        "date":   r["date"].strftime("%Y-%m-%d") if pd.notna(r["date"]) else None,
        "articleID": r["article_id"] if pd.notna(r["article_id"]) else None,
    }

def row_to_investment(r):
    # mirror row_to_capacity shape; only add 'investment' + 'event_type'
    # keep keys you already rely on (date/status/phase/product_lv1/product_lv2/article_id)
    return {
        "event_type": "investment",
        "date": r["date"].strftime("%Y-%m-%d") if pd.notna(r["date"]) else None,
        "status": r["status"],
        "phase": r["phase"],
        "product_lv1": r["product_lv1"],
        "product_lv2": list(r["product_lv2"]) if isinstance(r["product_lv2"], (list, tuple)) else [r["product_lv2"]],
        "investment": r["amount_EUR"],
        "investment_id": r.get("investment_id"),
        "articleID": r.get("article_id"),
    }