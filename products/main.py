import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

from transformers import pipeline
import re
from mongo_client import mongo_client, articles_collection
from datetime import datetime, timezone
from utils import combine_paragraphs
from functions import clean_text

from dotenv import load_dotenv
load_dotenv()

# define model architecture 

pipeline_version = "v0"
labels = ["battery", "biomass", "geothermal", "hydroelectric", "hydrogen", "nuclear", "solar", "steel", "vehicle", "wind"]
clf = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# define query: llm_processed must exist, and product_classifier_on must be absent or different
query = {
    "llm_processed": {"$exists": True},
    "$or": [
        {"product_classifier_on": {"$exists": False}},         # product classifier never run before
        {"product_classifier_on": {"$ne": pipeline_version}}   # product classifier run but an old version so we update
    ],
    "nodes": {
        "$elemMatch": {"type": "product"} }
    }

# Fetch entries to process
entries_to_process = list(articles_collection.find(query))
print(f"Found {len(entries_to_process)} entries to classify with version {pipeline_version}")

for article in entries_to_process[:2]:
    title = article["title"]
    print(f"Processing article: {title}")
    article_id = article["_id"]
    raw_text = combine_paragraphs(article)
    text = clean_text(raw_text)
    print(text)
    product_nodes = [node for node in article["nodes"] if node.get("type") == "product"]

    for product_node in product_nodes:
        product_name = product_node.get("name")
        if not product_name:
            continue

        premise = f"Item: {product_name}. Context: {text}"
        result = clf(premise, labels)

        product_node["technology"] = result["labels"][0]  # storing only the top result

    # update the entry, inclduing 
    articles_collection.update_one(
        {"_id": article_id},
        {"$set": {
            "nodes": article["nodes"],
            "product_classifier_on": pipeline_version,
            "product_classifier_updated_at": datetime.now(timezone.utc)
        }}
    )

print("Success")