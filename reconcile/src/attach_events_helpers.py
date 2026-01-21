import ast
import pandas as pd
from typing import Dict, List, Any, Tuple
from src.capex_dictionary import CAPEX_DICT

def normalize_pl2(val, lowercase: bool = False) -> List[str]:
    """
    Normalize product_lv2 value to a canonical sorted list.
    
    This is the single source of truth for pl2 normalization.
    Returns a list (MongoDB-friendly, JSON-serializable).
    Convert to tuple only when hashability is explicitly needed.
    
    Args:
        val: product_lv2 value (str, list, tuple, None, etc.)
        lowercase: If True, lowercase all values (for case-insensitive grouping)
        
    Returns:
        Sorted list of unique, trimmed, non-empty strings
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return []
    
    # Normalize to iterable
    if isinstance(val, (list, tuple, set)):
        vals = [v for v in val if v is not None and not (isinstance(v, float) and pd.isna(v))]
    else:
        vals = [val] if val is not None else []
    
    # Process: trim, filter empty, optionally lowercase
    processed = []
    for v in vals:
        s = str(v).strip()
        if s:  # Only include non-empty strings
            processed.append(s.lower() if lowercase else s)
    
    return sorted(set(processed))  # Unique, sorted list

def iso_date(dt) -> str | None:
    if pd.isna(dt): return None
    if isinstance(dt, str): return dt
    d = pd.to_datetime(dt, errors="coerce")
    return d.strftime("%Y-%m-%d") if pd.notna(d) else None

def capex_lookup(product_lv1: str, pl2_key: List[str] | Tuple[str, ...]) -> Dict[str, Any] | None:
    """Exact match on (product_lv1, product_lv2_key). Units are assumed normalized upstream."""
    # Normalize to tuple for comparison (handles both list and tuple inputs)
    pl2_tuple = tuple(pl2_key) if isinstance(pl2_key, list) else pl2_key
    for e in CAPEX_DICT.get("entries", []):
        e_pl2 = e.get("product_lv2_key")
        e_pl2_tuple = tuple(e_pl2) if isinstance(e_pl2, (list, tuple)) else (e_pl2,)
        if e.get("product_lv1") == product_lv1 and e_pl2_tuple == pl2_tuple:
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

def coerce_is_total(val) -> bool:
    """
    Normalize 'is_total' values to a strict boolean.

    Rules:
    - Explicit True stays True.
    - Strings like "true", "yes", "y", "1" → True.
    - Numeric 1 → True.
    - Everything else (False, 0, None, NaN, empty string) → False.
    """
    if val is True:
        return True
    if isinstance(val, str):
        return val.strip().lower() in {"true", "yes", "y", "1"}
    if isinstance(val, (int, float)) and not pd.isna(val):
        return int(val) == 1
    return False

def coerce_amount_scalar(val):
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
                return coerce_amount_scalar(parsed)
            except Exception:
                pass
        # numeric string with commas or spaces
        try:
            s_clean = s.replace(",", "").replace(" ", "")
            return float(s_clean), None
        except Exception:
            return None, None

    return None, None

def union_pl2_lists(lists: pd.Series) -> List[str]:
    """
    Union multiple pl2 lists (from pandas groupby) into one sorted list.
    
    Used during groupby aggregation to combine product_lv2 values that differ
    only by pl2 variants but are otherwise identical (same capacity, status, etc.).
    
    Args:
        lists: pandas Series of lists or tuples (each is a normalized pl2)
        
    Returns:
        Sorted list of unique values from all input lists/tuples
    """
    acc = set()
    for item in lists:
        if isinstance(item, (list, tuple)):
            acc.update(item)
        elif item:  # handle scalar strings
            acc.add(str(item).strip())
    return sorted(acc)

def _unit_capex(cap_rule: dict, phase: Any) -> float:
    """
    Return appropriate unit CAPEX, using retrofit-specific value when applicable.
    """
    base = float(cap_rule["capex_per_unit"])
    # Safely check if phase is "retrofit" (case-insensitive, handles whitespace)
    if isinstance(phase, str) and phase.strip().lower() == "retrofit" and "capex_per_unit_retrofit" in cap_rule:
        return float(cap_rule["capex_per_unit_retrofit"])
    return base