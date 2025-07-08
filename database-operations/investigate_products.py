#!/usr/bin/env python3
import sys; sys.path.append("..")
from mongo_client import articles_collection

# 1) CONNECT


# 2) DEFINE FILTER & PROJECTION
filter_ = {
    "nodes": {
        "$elemMatch": {
            "type": "product",
            "name": "electric car"
        }
    }
}
projection = {
    "_id": 0,
    "nodes": {
        "$elemMatch": {
            "type": "product",
            "name": "electric car"
        }
    }
}

# 3) RUN QUERY & COUNT
cursor = articles_collection.find(filter_, projection)

total_matched = 0
has_lv1 = 0
has_lv2 = 0
has_both = 0

for doc in cursor:
    total_matched += 1
    node = doc["nodes"][0]  # the matched product node
    lv1 = node.get("product_lv1")
    lv2 = node.get("product_lv2")
    
    if lv1 is not None:
        has_lv1 += 1
    if lv2 is not None:
        has_lv2 += 1
    if lv1 is not None and lv2 is not None:
        has_both += 1

# 4) PRINT RESULTS
print(f"Total documents matched: {total_matched}")
print(f"Documents with product_lv1: {has_lv1}")
print(f"Documents with product_lv2: {has_lv2}")
print(f"Documents with BOTH product_lv1 and product_lv2: {has_both}")