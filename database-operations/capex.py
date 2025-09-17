import sys; sys.path.append("..")
from mongo_client import facilities_collection
import pandas as pd
import math

pipeline = [
    # 1) explode capacity events
    {"$unwind": "$capacities"},

    # 2) keep only capacity events with an investment present (numeric)
    {"$match": {
        "capacities.event_type": "capacity",
        "capacities.investment": {"$type": "number"}  # excludes None/missing
    }},

    # 3) flatten into a single row
    {"$project": {
        "_id": 0,
        "investment": "$capacities.investment",
        "capacity": "$capacities.amount",
        "status": "$capacities.status",
        "phase": "$capacities.phase",
        "cap_product_lv1": "$capacities.product_lv1",
        "cap_product_lv2": "$capacities.product_lv2",
        "inst_canon": 1,
        "iso2": 1,
        "date": "$capacities.date",
        "project_id": 1,
        "articleID": "$capacities.articleID"
    }},

    # 4) optional: sort for readability
    {"$sort": {"iso2": 1, "investment": 1, "date": 1}}
]

docs = list(facilities_collection.aggregate(pipeline))

# (Optional) guard against NaN values slipping through
docs = [
    d for d in docs
    if not (isinstance(d.get("investment"), float) and math.isnan(d["investment"]))
]

# Load into pandas DataFrame
df = pd.DataFrame(docs)
df.to_excel("capex_test.xlsx")