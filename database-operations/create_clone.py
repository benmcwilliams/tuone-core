import sys; sys.path.append("..")
from mongo_client import mongo_client  # only import the client

from pymongo import InsertOne
import time

# ---------- Configuration ----------
SOURCE_DB_NAME = "tuone"
SOURCE_COLLECTION_NAME = "articles"
TARGET_DB_NAME = "tuone"
TARGET_COLLECTION_NAME = "test_articles"

# ---------- Setup ----------
source_collection = mongo_client[SOURCE_DB_NAME][SOURCE_COLLECTION_NAME]
target_collection = mongo_client[TARGET_DB_NAME][TARGET_COLLECTION_NAME]

# ---------- Clone ----------
print(f"Cloning from {SOURCE_DB_NAME}.{SOURCE_COLLECTION_NAME} → {TARGET_DB_NAME}.{TARGET_COLLECTION_NAME}")

start = time.time()

# Optional: clear the target first
target_collection.drop()
print("Target collection dropped (clean slate).")

docs = list(source_collection.find({}))
if not docs:
    print("❌ No documents found in source collection.")
    sys.exit(1)

target_collection.insert_many(docs)
print(f"✅ Copied {len(docs)} documents.")
print(f"⏱️ Done in {time.time() - start:.2f} seconds.")