import ast
import pandas as pd
from typing import Dict, List, Any, Tuple
from src.capex_dictionary import CAPEX_DICT

def pl2_tuple(val) -> Tuple[str, ...]:
    """Return a canonical tuple key for product_lv2 (handles str, list/tuple, None/NaN)."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ()
    if isinstance(val, (list, tuple, set)):
        vals = [v for v in val if v is not None and not (isinstance(v, float) and pd.isna(v))]
    else:
        vals = [val]
    # canonicalize to non-empty, trimmed strings, sorted
    vals = [str(v).strip() for v in vals if str(v).strip()]
    return tuple(sorted(vals))

def iso_date(dt) -> str | None:
    if pd.isna(dt): return None
    if isinstance(dt, str): return dt
    d = pd.to_datetime(dt, errors="coerce")
    return d.strftime("%Y-%m-%d") if pd.notna(d) else None

def norm_pl2_key(values) -> Tuple[str, ...]:
    if values is None or (isinstance(values, float) and pd.isna(values)):
        return ()
    if isinstance(values, str):
        vals = [values]
    elif isinstance(values, (list, tuple, set)):
        vals = list(values)
    else:
        vals = [values]  # catch any other scalar (e.g. int)
    vals = [v for v in vals if pd.notna(v)]
    return tuple(sorted({str(v).strip() for v in vals}))

def capex_lookup(product_lv1: str, pl2_key: Tuple[str, ...]) -> Dict[str, Any] | None:
    """Exact match on (product_lv1, product_lv2_key). Units are assumed normalized upstream."""
    for e in CAPEX_DICT.get("entries", []):
        if e.get("product_lv1") == product_lv1 and tuple(e.get("product_lv2_key") if isinstance(e.get("product_lv2_key"), (list, tuple)) else (e.get("product_lv2_key"),)) == pl2_key:
            return e
    return None

def sort_key(e: Dict[str, Any]):
    # Define explicit priority by event_type
    priority_map = {
        "capacity": 0,
        "investment": 1,
        "facility": 2,
    }
    d = iso_date(e.get("date"))
    # Fall back to lowest priority if unknown type
    priority = priority_map.get(e.get("event_type"), 99)
    return (d or "9999-12-31", priority)

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

# function to apply retrofit factor to capex if phase is retrofit
def _unit_capex(cap_rule: dict, phase: Any) -> float:
    """
    Return appropriate unit CAPEX, using retrofit-specific value when applicable.
    """
    base = float(cap_rule["capex_per_unit"])
    if (phase or "").strip().lower() == "retrofit" and "capex_per_unit_retrofit" in cap_rule:
        return float(cap_rule["capex_per_unit_retrofit"])
    return base