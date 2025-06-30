import sys; sys.path.append("..")
import os
import time
from datetime import datetime, timezone

from transformers import pipeline
import re
from mongo_client import mongo_client, articles_collection
from utils import combine_paragraphs
from reconcile.src.products_utils import clean_text
from dotenv import load_dotenv

load_dotenv()

import logging

def get_article_logger(article_id: str) -> logging.Logger:
    logger = logging.getLogger(str(article_id))
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers in repeated runs
    if not logger.handlers:
        file_handler = logging.FileHandler(os.path.join(log_dir, f"{article_id}.log"), mode='w')
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Base log folder
log_dir = "logs/logs_articles"
os.makedirs(log_dir, exist_ok=True)

# ----------- Timing: Start Clock -----------
global_start = time.time()
print(f"Script started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ----------- Model Setup -----------

pipeline_version = "v0"
labels = ["battery", "biomass", "geothermal", "hydroelectric", "hydrogen", "nuclear", "solar", "steel", "vehicle", "wind"]
clf = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# ----------- MongoDB Query -----------
#ADD LOGIC that the product must be connected to a factory? 
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
    article_id = article["_id"]
    print(f"\n[{idx}/{len(entries_to_process)}] Processing article: {title}")

    logger = get_article_logger(article_id)  # create logger for this article
    logger.info(f"{title}")

    raw_text = combine_paragraphs(article)
    text = clean_text(raw_text)

    product_nodes = [node for node in article["nodes"] if node.get("type") == "product"]
    logger.info(f"Found {len(product_nodes)} product node(s)")

    product_ids_with_produced_at = set(
    rel["source"] for rel in article["relationships"]
    if rel.get("type") == "produced_at")
    logger.info(f"Found {len(product_ids_with_produced_at)} product node(s) with a 'produced_at' relationship")

    for product_node in product_nodes:

        product_name = product_node.get("name")
        if not product_name:
            logger.warning("Skipping unnamed product node.")
            continue

        if product_node["id"] not in product_ids_with_produced_at:
            logger.info(f"Skipping product '{product_name}' (not linked via 'produced_at')")
            continue  # skip classification

        premise = f"Item: {product_name}. Context: {text}"
        result = clf(premise, labels)

        predicted_label = result["labels"][0]
        product_node["technology"] = predicted_label  # storing only the top result
        logger.info(f"✓ Classified '{product_name}' → {predicted_label}")

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