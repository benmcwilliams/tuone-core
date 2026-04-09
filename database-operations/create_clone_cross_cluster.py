"""
Clone a collection from source cluster (tuone) to target cluster (opensource).
Uses mongo_client_clone: MONGO_URI_TUONE / MONGO_DB_NAME_TUONE for source,
MONGO_URI / MONGO_DB_NAME for target.

Run from project root. Only the root .env is used (not any .env under database-operations).
  python database-operations/create_clone_cross_cluster.py
"""
import sys
import time
import os
from pathlib import Path

# Use project root .env only (avoids confusion with database-operations/.env if present)
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))
os.chdir(_project_root)

from dotenv import load_dotenv
load_dotenv(_project_root / ".env")
from mongo_client_clone import source_client, get_target_client

# ---------- Configuration ----------
#SOURCE_DB_NAME = os.getenv("MONGO_DB_NAME_TUONE", "tuone")
#TARGET_DB_NAME = os.getenv("MONGO_DB_NAME", "opensourcedev")

# Set up to copy from opensource dev into opensource

SOURCE_DB_NAME = 'opensource'
SOURCE_COLLECTION_NAME = "electricity"

TARGET_DB_NAME = 'opensourcedev'
TARGET_COLLECTION_NAME = "electricity"
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
