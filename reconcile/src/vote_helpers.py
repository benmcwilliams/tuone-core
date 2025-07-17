import ast
import numpy as np

# cases where only one unique product_lv2 is noted within a GROUP. 
# we replace all NaN values with that value 
# IF more than one unique product_lv2 no changes are made. 

def fill_single_product_lv2(group):
    unique_vals = group["product_lv2"].dropna().unique()
    if len(unique_vals) == 1:
        group["product_lv2"] = group["product_lv2"].fillna(unique_vals[0])
    return group

# parse capacity column - midpoint of lists and clean any NA values etc

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