import sys; sys.path.append("..")
import pandas as pd
from mongo_client import facilities_collection

# Fetch all documents
docs = list(facilities_collection.find({}, {
    "phases": 1,
    "inst_canon": 1,
    "iso2": 1,
    "admin_group_key": 1,
    "product_lv1": 1,
    "product_lv2": 1,
    "main.status": 1
}))

# Flatten and combine
rows = []
for d in docs:
    main_status = d.get("main", {}).get("status")
    base = {
        "inst_canon": d.get("inst_canon"),
        "iso2": d.get("iso2"),
        "admin_group_key": d.get("admin_group_key"),
        "product_lv1": d.get("product_lv1"),
        "main_status": main_status,
    }
    for ph in d.get("phases", []):
        for pl2 in d.get("product_lv2", []):
            rows.append({**base, "product_lv2": pl2, **ph})

# Create DataFrame & write master to Rhodium
df = pd.DataFrame(rows)
companyNames = pd.read_excel("storage/input/CompanyNames.xlsx")
df = df.merge(companyNames, on="inst_canon", how="left")
df.to_excel("rhodium_format.xlsx")

# battery cell simple output 

df_cell = df[
    (df["product_lv1"] == "battery") &
    (df["product_lv2"] == "cell") &
    (~df["main_status"].isin(["paused", "cancelled"]))
].copy()

df_cell.to_excel("rhodium_cell.xlsx")

