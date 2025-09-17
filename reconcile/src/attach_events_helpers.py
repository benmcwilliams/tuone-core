import ast
import pandas as pd

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