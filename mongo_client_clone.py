"""
MongoDB clients for cross-cluster clone operations.
Source = MONGO_URI from .env. Target = MONGO_URI_OPEN_SOURCE in .env.
"""
import os
import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

# Source cluster (existing .env)
MONGO_URI_SOURCE = os.getenv("MONGO_URI")
if not MONGO_URI_SOURCE:
    raise RuntimeError("❌ MONGO_URI not set. Set it in .env for the source cluster.")

# Target cluster (set MONGO_URI_OPEN_SOURCE in .env)
MONGO_URI_TARGET = (os.getenv("MONGO_URI_OPEN_SOURCE") or "").strip()

source_client = MongoClient(
    MONGO_URI_SOURCE, server_api=ServerApi("1"), tlsCAFile=certifi.where()
)
target_client = (
    MongoClient(
        MONGO_URI_TARGET, server_api=ServerApi("1"), tlsCAFile=certifi.where()
    )
    if MONGO_URI_TARGET
    else None
)


def get_target_client():
    if target_client is None:
        raise RuntimeError(
            "❌ Target cluster URI not set. Set MONGO_URI_TARGET or MONGO_URI_OPEN_SOURCE in .env."
        )
    return target_client
