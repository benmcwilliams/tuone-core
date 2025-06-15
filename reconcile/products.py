import sys
import os
import time
from datetime import datetime, timezone

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from transformers import pipeline
import re
from mongo_client import mongo_client, articles_collection
from utils import combine_paragraphs
from reconcile.src.products_utils import clean_text
from dotenv import load_dotenv

load_dotenv()

# ----------- Timing: Start Clock -----------
global_start = time.time()
print(f"Script started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ----------- Model Setup -----------

pipeline_version = "v0"
labels = ["battery", "biomass", "geothermal", "hydroelectric", "hydrogen", "nuclear", "solar", "steel", "vehicle", "wind"]
clf = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# ----------- MongoDB Query -----------
query = {
    "llm_processed": {"$exists": True},
    "$or": [
        {"product_classifier_on": {"$exists": False}},       #product classifier never run before
        {"product_classifier_on": {"$ne": pipeline_version}} #product classifier run on an old version
    ],
    "$and": [
        {"nodes": {"$elemMatch": {"type": "product"}}},      #a product node is present
        {"nodes": {
            "$elemMatch": {
                "type": {"$in": ["investment", "capacity"]}  #at least one of investment | capacity are present
            }
        }}
    ]
}

entries_to_process = list(articles_collection.find(query))
print(f"Found {len(entries_to_process)} entries to classify with version {pipeline_version}")

# ----------- Main Processing Loop -----------
for idx, article in enumerate(entries_to_process, 1):
    article_start = time.time()

    title = article["title"]
    print(f"\n[{idx}/{len(entries_to_process)}] Processing article: {title}")
    article_id = article["_id"]
    raw_text = combine_paragraphs(article)
    text = clean_text(raw_text)
    product_nodes = [node for node in article["nodes"] if node.get("type") == "product"]

    for product_node in product_nodes:
        product_name = product_node.get("name")
        if not product_name:
            continue

        premise = f"Item: {product_name}. Context: {text}"
        result = clf(premise, labels)

        product_node["technology"] = result["labels"][0]  # storing only the top result

    articles_collection.update_one(
        {"_id": article_id},
        {"$set": {
            "nodes": article["nodes"],
            "product_classifier_on": pipeline_version,
            "product_classifier_updated_at": datetime.now(timezone.utc)
        }}
    )

    elapsed = time.time() - article_start
    print(f"→ Finished in {elapsed:.2f} seconds")

# ----------- Done -----------
total_time = time.time() - global_start
print(f"\n✅ Success — total time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")