# mongo_client_setup.py
import os
import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import logging

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
ARTICLES_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME")
FACILITIES_COLLECTION = os.getenv("MONGO_FACILITIES_COLLECTION")

if not all([MONGO_URI, DB_NAME, ARTICLES_COLLECTION_NAME]):
    raise RuntimeError("❌ Missing required MongoDB environment variables.")

mongo_client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
db = mongo_client[DB_NAME]
articles_collection = db[ARTICLES_COLLECTION_NAME]
facilities_collection = db[FACILITIES_COLLECTION]
geonames_collection = db["geonames_lookup"]
geonames_collection = db["geonames_store"]

def test_mongo_connection():
    try:
        mongo_client.admin.command("ping")
        print("✅ Connected to MongoDB Atlas!")
    except Exception as e:
        print(f"❌ MongoDB Connection Error: {e}")
        raise