import sys; sys.path.append("..")
from mongo_client import articles_collection

pipeline = [
    {"$unwind": "$nodes"},              # return all nodes
    {"$unwind": "$relationships"},      # return all relationships
    {"$match": {
        "nodes.type": "product",                # limit to only product nodes
        "relationships.type": "quantifies",     # limit to only quantify relationships
        "$expr": {
            "$or": [
                {"$eq": ["$relationships.source", "$nodes.id"]},    # product node must be connected to a quantify relationship
                {"$eq": ["$relationships.target", "$nodes.id"]}
            ]
        }
    }},
    {"$project": {
        "_id": 0,
        "name": "$nodes.name",
        "product_lv1": "$nodes.product_lv1",
        "product_lv2": "$nodes.product_lv2",
        "product_lv3": "$nodes.product_lv3",
        "article_id": {"$toString": "$_id"}
    }},
    {"$group": {
        "_id": {
            "name": "$name",
            "product_lv1": "$product_lv1",
            "product_lv2": "$product_lv2",
            "product_lv3": "$product_lv3"
        },
        "article_ids": {"$addToSet": "$article_id"}
    }},
    {"$project": {
        "_id": 0,
        "name": "$_id.name",
        "product_lv1": "$_id.product_lv1",
        "product_lv2": "$_id.product_lv2",
        "product_lv3": "$_id.product_lv3",
        # keep only 5 article IDs (anymore is for examples that are super obvious)
        "article_ids": {"$slice": ["$article_ids", 5]}
    }},
    {"$sort": {"name": 1, "product_lv1": 1, "product_lv2": 1, "product_lv3": 1}}
]

cursor = articles_collection.aggregate(pipeline)
products = list(cursor)

# quick check
print(products[:5])