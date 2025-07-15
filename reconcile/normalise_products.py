import sys; sys.path.append("..")
import pandas as pd 
from mongo_client import articles_collection
from pymongo import UpdateMany
import logging

product_classification_file = "storage/input/product_classification.xlsx"

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    handlers=[logging.FileHandler("product_update.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# read existing product excel dictionary 

df = pd.read_excel(product_classification_file)
existing_products = df["product"].tolist() 

# filter df to products that have at least level 1 mapped (these will be written to the mongodb)
df_lv1 = df[~df['product_lv1'].isna()].copy()          
updates = df_lv1.set_index("product").to_dict(orient="index")

# compare to all products (that are used to QUANTIFY a capacity) in mongoDB

pipeline = [
    # 1) explode the nodes array
    {"$unwind": "$nodes"},
    # 2) explode the relationships array
    {"$unwind": "$relationships"},
    # 3) keep only product‐type nodes AND only QUANTIFY relationships
    #    where the node’s id is either the source or the target
    {"$match": {
        "nodes.type": "product",
        "relationships.type": "quantifies",
        "$expr": {
            "$or": [
                {"$eq": ["$relationships.source", "$nodes.id"]},
                {"$eq": ["$relationships.target", "$nodes.id"]}
            ]
        }
    }},
    # 4) group back by product name to get uniqueness
    {"$group": {"_id": "$nodes.name"}},
    # 5) reshape for a clean output
    {"$project": {"_id": 0, "name": "$_id"}}
]

cursor = articles_collection.aggregate(pipeline)
product_mongo = [doc["name"] for doc in cursor]

# 3 - output those products that are not yet mapped & should be 

new_products = [p for p in product_mongo if p not in existing_products]

new_products_df = pd.DataFrame({
    "product": new_products,
    "product_lv1": [None] * len(new_products),
    "product_lv2": [None] * len(new_products)
})

df_out = pd.concat([df,new_products_df])
df_out.sort_values(by="product",inplace=True)

# concat the dataframes and output back to the same dataframe. We can update from here. 
df_out.to_excel(product_classification_file,index=False)

# 4 - update all product values in mongodb
processed = 0
bulk_ops = []

for product_name, payload in updates.items():
    processed += 1
    filter_ = {"nodes": {"$elemMatch": {"type": "product", "name": product_name}}}

    ## DEBUGGING CODE BELOW (in case anything strange happening during update)

    # # 1) count how many docs match this product
    match_count = articles_collection.count_documents(filter_)
    logger.info(
        f"🔎 [{processed}/{len(updates)}] product={product_name!r} → "
        f"{match_count} document(s) matched"
    )

    # if match_count:
    #     # Peek at up to 3 matched docs, including existing lv1/lv2
    #     cursor = articles_collection.find(
    #         filter_,
    #         {
    #             "_id": 1,
    #             "nodes": {
    #                 "$elemMatch": {"type": "product", "name": product_name}
    #             }
    #         }
    #     ).limit(3)

    #     for doc in cursor:
    #         node = doc["nodes"][0]
    #         existing_lv1 = node.get("product_lv1")
    #         existing_lv2 = node.get("product_lv2")
    #         logger.info(
    #             f"   • doc_id={doc['_id']} node before update: "
    #             f"lv1={existing_lv1!r} (→ {payload['product_lv1']!r}), "
    #             f"lv2={existing_lv2!r} (→ {payload['product_lv2']!r})"
    #         )
    # else:
    #     logger.warning(f"   ⚠️ No documents found for product={product_name!r}")

    # 2) queue the update op
    bulk_ops.append(
        UpdateMany(
            filter_,
            {"$set": {
                "nodes.$[elem].product_lv1": payload["product_lv1"],
                "nodes.$[elem].product_lv2": payload["product_lv2"],
            }},
            array_filters=[{"elem.type": "product", "elem.name": product_name}],
            upsert=False
        )
    )

# commit in batches (500 each) not to overload server
total_matched = 0
total_modified = 0

for batch_idx in range(0, len(bulk_ops), 500):
    batch = bulk_ops[batch_idx : batch_idx + 500]
    result = articles_collection.bulk_write(batch)
    matched = result.matched_count
    modified = result.modified_count

    total_matched += matched
    total_modified += modified

    logger.info(
        f"✅ Batch {batch_idx//500 + 1}: "
        f"submitted={len(batch)}, matched={matched}, modified={modified}"
    )

# 3) Final summary across all batches
logger.info(
    f"🎉 All done: processed={processed}, "
    f"total_matched={total_matched}, total_modified={total_modified}"
)

