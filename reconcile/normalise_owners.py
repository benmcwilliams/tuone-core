import sys; sys.path.append("..")
from mongo_client import articles_collection
from pymongo import UpdateMany
from reconcile.src.step_1 import TextCleaner
import pandas as pd
import logging

def clean_owner_names():

    """Cleans and standardizes company names from MongoDB nodes using TextCleaner."""

    # text cleaner class - we use clean_string function
    cleaner = TextCleaner()

    # 1. return logging info on how many company | JVs have already been processed and how many remains
    total_names = articles_collection.aggregate([
        {"$unwind": "$nodes"}, # explode the nodes array
        {"$match": {"nodes.type": {"$in": ["joint_venture", "company"]}}}, # include only company & JV nodes
        {"$group": {"_id": "$nodes.name"}}, # group by node name to return a unique list, deduplicates the list
        {"$count": "total"} # return total 
    ])
    total_names = list(total_names)[0]["total"]

    with_name_canon = articles_collection.aggregate([
        {"$unwind": "$nodes"},
        {"$match": {
            "nodes.type": {"$in": ["joint_venture", "company"]},
            "nodes.name_canon": {"$exists": True, "$ne": None}
        }},
        {"$group": {"_id": "$nodes.name"}},
        {"$count": "with_name_canon"}
    ])
    with_name_canon = list(with_name_canon)[0]["with_name_canon"]

    logging.info(f"🔢 {total_names} company or joint_venture nodes present")
    logging.info(f"🟢 of which {with_name_canon} already have name_canon. {total_names-with_name_canon} need processing")

    # 2. returning selection of company | JV names that should be processed

    pipeline = [
        {"$unwind": "$nodes"}, # explode nodes
        {"$match": {
            "nodes.type": {"$in": ["joint_venture", "company"]},    # include only company or joint_ventures
            "$or": [
                {"nodes.name_canon": {"$exists": False}},           # if they do not already have name_canon processed
                {"nodes.name_canon": None}
            ]
        }},
        {"$group": {"_id": "$nodes.name"}},                         # deduplicate the list
        {"$project": {"_id": 0, "name": "$_id"}}
    ]

    cursor = articles_collection.aggregate(pipeline)
    company_mongo = [doc["name"] for doc in cursor]

    # 3. build bulk update operations
    ops = []
    for raw_name in company_mongo:
        if not isinstance(raw_name, str) or not raw_name.strip() or pd.isna(raw_name):
            continue

        canon = cleaner.clean_string(raw_name)
        if canon is None or pd.isna(canon):
            continue

        ops.append(
            UpdateMany(
                # Match only documents that have at least one matching element
                # with this raw name AND where name_canon is still missing.
                # CHANGED: Added the `$or: exists False / None` guard to avoid touching already-processed docs.
                {
                    "nodes": {
                        "$elemMatch": {
                            "type": {"$in": ["joint_venture", "company"]},
                            "name": raw_name,
                            "$or": [
                                {"name_canon": {"$exists": False}},   # CHANGED
                                {"name_canon": None}                   # CHANGED
                            ]
                        }
                    }
                },
                # Set the canonical value…
                {
                    "$set": {"nodes.$[c].name_canon": canon}
                },
                # …but only on array elements that still lack it.
                # CHANGED: Added the same guard inside array_filters to prevent re-writes.
                array_filters=[{
                    "c.type": {"$in": ["joint_venture", "company"]},
                    "c.name": raw_name,
                    "$or": [
                        {"c.name_canon": {"$exists": False}},       # CHANGED
                        {"c.name_canon": None}                       # CHANGED
                    ]
                }]
            )
        )

    # 4. execute update in batches
    BATCH_SIZE = 500
    logging.info(f"{len(ops)} updates to be committed to mongoDB.")

    for i in range(0, len(ops), BATCH_SIZE):
        batch = ops[i : i + BATCH_SIZE]
        result = articles_collection.bulk_write(batch) # can add ordered=False to make even quicker
        logging.info(f"Batch {i//BATCH_SIZE}: matched {result.matched_count}, modified {result.modified_count}")