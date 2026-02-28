import sys
import time
import os
sys.path.append("..")
from dotenv import load_dotenv
load_dotenv()
from mongo_client import mongo_client

# ---------- Configuration ----------
DB_NAME = os.getenv("MONGO_DB_NAME", "opensourcedev")
SOURCE_DB_NAME = DB_NAME
SOURCE_COLLECTION_NAME = "facilities"
TARGET_DB_NAME = DB_NAME
TARGET_COLLECTION_NAME = "facilities_0112"
BATCH_SIZE = 1000

# ---------- Setup ----------
source_collection = mongo_client[SOURCE_DB_NAME][SOURCE_COLLECTION_NAME]
target_collection = mongo_client[TARGET_DB_NAME][TARGET_COLLECTION_NAME]

# ---------- Clone ----------
print(f"Cloning from {SOURCE_DB_NAME}.{SOURCE_COLLECTION_NAME} → {TARGET_DB_NAME}.{TARGET_COLLECTION_NAME}")

start = time.time()

# Optional: clear the target first
target_collection.drop()
print("Target collection dropped (clean slate).")

# Use regular cursor (no no_cursor_timeout)
cursor = source_collection.find({})
batch = []
count = 0

for doc in cursor:
    batch.append(doc)
    if len(batch) == BATCH_SIZE:
        target_collection.insert_many(batch)
        count += len(batch)
        print(f"✅ Inserted batch of {len(batch)} docs. Total: {count}")
        batch = []

# Insert any remaining docs
if batch:
    target_collection.insert_many(batch)
    count += len(batch)
    print(f"✅ Inserted final batch of {len(batch)} docs. Total: {count}")

print(f"✅ Done. Total inserted: {count}")
print(f"⏱️ Elapsed time: {time.time() - start:.2f} seconds")