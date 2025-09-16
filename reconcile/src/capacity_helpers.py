import pandas as pd
import sys; sys.path.append("..")
from src.capacity_constants import KEYWORD_MULTIPLIER_MAP, DEFAULT_UNIT_MAP

# ========= Load Excel =========
def load_capacity_column(file_path):
    df = pd.read_excel(file_path)
    df["capacity"] = df["capacity"].fillna("")
    return df

def get_default_unit(product_lv1: str | None, product_lv2: str | None) -> str:
    """
    Returns the configured default unit for a product category.
    Lookup tries (lv1, lv2) first, then (lv1, None). Falls back to 'gigawatt hour'.
    """
    lv1 = (product_lv1 or None)
    if isinstance(lv1, str):
        lv1 = lv1.strip().lower() or None
    lv2 = (product_lv2 or None)
    if isinstance(lv2, str):
        lv2 = lv2.strip().lower() or None

    return (
        DEFAULT_UNIT_MAP.get((lv1, lv2))
        or DEFAULT_UNIT_MAP.get((lv1, None))
        or "gigawatt hour"
    )

def detect_keyword_multiplier(text_lower: str):
    """
    Scan KEYWORD_MULTIPLIER_MAP once and return the first match found.
    Returns (multiplier, matched_keyword, keywords_tuple) or (None, None, None).
    """
    for keywords, mult in KEYWORD_MULTIPLIER_MAP.items():
        for k in keywords:
            if k in text_lower:
                return mult, k, keywords
    return None, None, None

def _as_iter(x):
    return x if isinstance(x, (list, tuple)) else [x]

def has_nan(value):
    """True if value is None/NaN or any element is NaN for list/tuple."""
    if value is None:
        return True
    if isinstance(value, (list, tuple)):
        return any(pd.isna(v) for v in value)
    return bool(pd.isna(value))

def apply_scale(value, scale):
    if value is None:
        return None
    out = []
    for v in _as_iter(value):
        try:
            out.append(float(v) * (scale or 1))
        except Exception:
            return None
    return out if isinstance(value, (list, tuple)) else out[0]

def annualize(value, time):
    if value is None:
        return None
    factor = {"per day": 365, "per week": 52, "per month": 12}.get((time or "").strip().lower(), 1)
    out = []
    for v in _as_iter(value):
        out.append(v * factor)
    return out if isinstance(value, (list, tuple)) else out[0]



def multiply_vals(value, mult):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    out = []
    for v in _as_iter(value):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            out.append(None)
        else:
            out.append(v * mult)

    return out if isinstance(value, (list, tuple)) else out[0]


def metric_is_missing(metric):
    s = "" if metric is None else str(metric).strip().lower()
    return (s in {"", "nan", "none", "unit"}) or (pd.isna(metric) if metric is not None else True)