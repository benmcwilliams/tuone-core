import sys; sys.path.append("..")
from pymongo import MongoClient
import pandas as pd
from mongo_client import facilities_collection
from src.config import CAPACITIES_PLOT

def output_capacities_plot():

    pipeline = [
        {"$project": {
            "_id": 0,
            "owner": "$inst_canon",          # rename
            "iso2": 1,
            "adm1": 1,
            "product_lv1": 1,
            "product_lv2": 1,                # << add this
            "greenfield_status": "$greenfield.status",
            "greenfield_capacity": "$greenfield.capacity",
            "greenfield_announced_on": "$greenfield.announced_on",
            "greenfield_under_construction_on": "$greenfield.under_construction_on",
            "greenfield_operational_on": "$greenfield.operational_on",
        }}
    ]

    rows = list(facilities_collection.aggregate(pipeline))
    df = pd.DataFrame(rows)

    # --- minimal: ensure list + explode
    df["product_lv2"] = df["product_lv2"].apply(lambda x: x if isinstance(x, list) else ([x] if x is not None else [pd.NA]))
    df = df.explode("product_lv2", ignore_index=True)

    # Optional: parse dates + make NaNs proper
    date_cols = ["greenfield_announced_on", "greenfield_under_construction_on", "greenfield_operational_on"]  # include operations
    for c in date_cols:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    # If capacity is sometimes stored as BSON Double NaN, pandas will already see it as np.nan
    # but if it was a dict (rare), coerce:
    if "greenfield_capacity" in df.columns and df["greenfield_capacity"].dtype == "object":
        df["greenfield_capacity"] = pd.to_numeric(df["greenfield_capacity"], errors="coerce")

    print(df.head())

    df.to_excel(CAPACITIES_PLOT)