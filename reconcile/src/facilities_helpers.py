import numpy as np
import pandas as pd
import ast

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
        "investment": r.get("investment"),
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
        "investment": r["investment"],
        "articleID": r.get("article_id"),
    }