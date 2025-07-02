import sys; sys.path.append("..")
import os
import time
import logging
from datetime import datetime, timezone
from mongo_client import mongo_client, test_articles_collection
from reconcile.src.step_2 import standardize_country, get_adm_level
from dotenv import load_dotenv

load_dotenv()

query = {
    "meta.category": "electrive",
    "nodes": {
        "$elemMatch": {
            "type": "factory",
            "location.city": {"$exists": True, "$nin": [None, "", "null", "nan"]},
            "location.country": {"$exists": True, "$nin": [None, "", "null", "nan"]},
        }
    }
}

entries = list(test_articles_collection.find(query))
print(f"Found {len(entries)} article(s) with unenriched factory location(s)")