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