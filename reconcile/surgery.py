import sys; sys.path.append("..")
from pymongo import UpdateOne
from mongo_client import test_articles_collection

# Define all the enriched fields
fields_to_unset = [
    "location.factory_city_latitude",
    "location.factory_city_longitude",
    "location.factory_city_adm_level",
    "location.factory_city_not_found",
    "location.country_standardized",
    "location.country_iso2",
    "location.country_not_found",
] + [
    f"location.factory_city_adm{level}_{suffix}"
    for level in range(1, 6)
    for suffix in ["name", "code"]
]

# Query to find articles where any of those exist
query = {
    "nodes": {
        "$elemMatch": {
            "type": "factory",
            "$or": [{field: {"$exists": True}} for field in fields_to_unset]
        }
    }
}

docs = list(test_articles_collection.find(query))
print(f"Found {len(docs)} article(s) with enriched factory fields to reset.")

# Prepare bulk operations
ops = []
for doc in docs:
    updated_nodes = []
    changed = False
    for node in doc["nodes"]:
        if node.get("type") != "factory" or "location" not in node:
            updated_nodes.append(node)
            continue

        loc = node["location"]
        for field in fields_to_unset:
            key = field.split(".", 1)[1]
            if key in loc:
                del loc[key]
                changed = True

        updated_nodes.append(node)

    if changed:
        ops.append(UpdateOne(
            {"_id": doc["_id"]},
            {"$set": {"nodes": updated_nodes},
             "$unset": {"factory_geonames_enriched_at": ""}}
        ))

# Execute bulk update
if ops:
    result = test_articles_collection.bulk_write(ops)
    print(f"✅ Reset fields in {result.modified_count} document(s)")
else:
    print("Nothing to update.")