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
FACILITIES_COLLECTION = "facilities"
FACILITIES_NATURE = "facilities_nature_submission_april26"


if not all([MONGO_URI, DB_NAME, ARTICLES_COLLECTION_NAME]):
    raise RuntimeError("❌ Missing required MongoDB environment variables.")

mongo_client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
db = mongo_client[DB_NAME]
articles_collection = db[ARTICLES_COLLECTION_NAME]
facilities_collection = db[FACILITIES_COLLECTION]
facilities_collection_nature = db[FACILITIES_NATURE]
geonames_collection = db["geonames_store"]
# Optional test/articles clone collection (e.g. for database-operations/surgery.py)
test_articles_collection = db[os.getenv("MONGO_TEST_ARTICLES_COLLECTION", "articles_clone")]

def test_mongo_connection():
    try:
        mongo_client.admin.command("ping")
        #print("✅ Connected to MongoDB Atlas!")
    except Exception as e:
        print(f"❌ MongoDB Connection Error: {e}")
        raise
