import ast
import pandas as pd
from typing import Dict, List, Any, Tuple
from src.capex_dictionary import CAPEX_DICT

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

def coerce_amount_eur_scalar(val):
    """
    Return (scalar_float_or_None, policy_str_or_None).
    - Lists/tuples -> pick max numeric (policy 'max_available').
    - Stringified lists -> parse then same as above.
    - Numeric strings with commas -> strip and parse.
    - Plain float/int -> return as float.
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None, None

    # If it's already numeric
    if isinstance(val, (int, float)) and not pd.isna(val):
        return float(val), None

    # If it's a list/tuple
    if isinstance(val, (list, tuple)):
        nums = [float(x) for x in val if isinstance(x, (int, float)) and not pd.isna(x)]
        if nums:
            return max(nums), "max_available"
        return None, None

    # If it's a string: try to parse list first, then numeric
    if isinstance(val, str):
        s = val.strip()
        # stringified list like "[None, 2000000000.0]"
        if (s.startswith("[") and s.endswith("]")) or (s.startswith("(") and s.endswith(")")):
            try:
                parsed = ast.literal_eval(s)
                return coerce_amount_eur_scalar(parsed)
            except Exception:
                pass
        # numeric string with commas or spaces
        try:
            s_clean = s.replace(",", "").replace(" ", "")
            return float(s_clean), None
        except Exception:
            return None, None

    return None, None