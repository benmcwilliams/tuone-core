import sys; sys.path.append("..")
from mongo_client import articles_collection
from pymongo import UpdateMany
from reconcile.src.step_1 import TextCleaner
import pandas as pd

# text cleaner class - we use clean_string function
cleaner = TextCleaner()

# returning all company names from nodes in mongo_db
pipeline = [
    # explode the nodes array
    {"$unwind": "$nodes"},
    # explode the relationships array
    {"$unwind": "$relationships"},
    # keep only company‐type nodes AND only OWNS relationships
     {"$match": {"nodes.type": {"$in": ["joint_venture", "company"]}}},
    # group back by product name to get uniqueness
    {"$group": {"_id": "$nodes.name"}},
    # reshape for a clean output
    {"$project": {"_id": 0, "name": "$_id"}}
]

cursor = articles_collection.aggregate(pipeline)
company_mongo = [doc["name"] for doc in cursor]

# build bulk update operations
ops = []
for raw_name in company_mongo:

    if not isinstance(raw_name, str) or not raw_name.strip() or pd.isna(raw_name):
        continue

    canon = cleaner.clean_string(raw_name)

    if canon is None or pd.isna(canon):
        continue

    ops.append(
        UpdateMany(
            # match any doc with a company node having this raw name
            {"nodes": {"$elemMatch": {"type": "company", "name": raw_name}}},
            # set the new name_canon field on that array element
            {"$set": {"nodes.$[c].name_canon": canon}},
            array_filters=[{"c.type": "company", "c.name": raw_name}]
        )
    )

# execute in batches
BATCH_SIZE = 500
for i in range(0, len(ops), BATCH_SIZE):
    batch = ops[i : i + BATCH_SIZE]
    result = articles_collection.bulk_write(batch)
    print(f"Batch {i//BATCH_SIZE}: matched {result.matched_count}, modified {result.modified_count}")