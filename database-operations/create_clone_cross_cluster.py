"""
Clone a collection from source cluster to target cluster.
Uses mongo_client_clone: set MONGO_URI_TARGET in .env or paste URI in mongo_client_clone.py.
"""
import sys
import time

sys.path.append("..")
from mongo_client_clone import source_client, get_target_client

# ---------- Configuration ----------
SOURCE_DB_NAME = "tuone"
SOURCE_COLLECTION_NAME = "facilities"
TARGET_DB_NAME = "opensourcedev"
TARGET_COLLECTION_NAME = "facilities"
BATCH_SIZE = 1000

# ---------- Setup ----------
source_collection = source_client[SOURCE_DB_NAME][SOURCE_COLLECTION_NAME]
target_client = get_target_client()
target_collection = target_client[TARGET_DB_NAME][TARGET_COLLECTION_NAME]

# ---------- Clone ----------
print(
    f"Cloning (cross-cluster) from {SOURCE_DB_NAME}.{SOURCE_COLLECTION_NAME} → {TARGET_DB_NAME}.{TARGET_COLLECTION_NAME}"
)

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
