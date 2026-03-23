"""
MongoDB clients for cross-cluster clone operations (e.g. tuone → opensource).

- Source cluster: MONGO_URI_TUONE in .env (legacy tuone). If unset, falls back to MONGO_URI.
- Target cluster: MONGO_URI in .env (main app cluster = opensource/opensourcedev after migration).

Use for scripts that copy collections from the legacy tuone cluster to the default cluster.
"""
import os
import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

# Source: legacy tuone cluster when cloning to opensource; else same as main
MONGO_URI_TUONE = (os.getenv("MONGO_URI_TUONE") or os.getenv("MONGO_URI") or "").strip()

# Target: main app cluster (opensource after migration)
MONGO_URI_OPENSOURCE = (os.getenv("MONGO_URI") or "").strip()

if not MONGO_URI_TUONE:
    raise RuntimeError("❌ MONGO_URI or MONGO_URI_TUONE not set in .env.")
if not MONGO_URI_OPENSOURCE:
    raise RuntimeError("❌ MONGO_URI not set in .env (target cluster for clones).")

source_client = MongoClient(
    MONGO_URI_OPENSOURCE, server_api=ServerApi("1"), tlsCAFile=certifi.where()
)
target_client = MongoClient(
    MONGO_URI_OPENSOURCE, server_api=ServerApi("1"), tlsCAFile=certifi.where()
)


def get_target_client():
    return target_client
