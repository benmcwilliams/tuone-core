import pandas as pd

# ========= Load Excel =========
def load_capacity_column(file_path):
    df = pd.read_excel(file_path)
    df["capacity"] = df["capacity"].fillna("")
    return df

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
    if value is None:
        return None
    out = []
    for v in _as_iter(value):
        out.append(v * mult)
    return out if isinstance(value, (list, tuple)) else out[0]