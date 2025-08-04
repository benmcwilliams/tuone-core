# mongo_client_setup.py
import os
import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
ARTICLES_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME")
TEST_ARTICLES_COLLECTION = os.getenv("MONGO_TEST_ARTICLES_NAME")
CAPACITIES_COLLECTION = os.getenv("MONGO_CAPICITIES_COLLECTION")
FACILITIES_COLLECTION = os.getenv("MONGO_FACILITIES_COLLECTION")

if not all([MONGO_URI, DB_NAME, ARTICLES_COLLECTION_NAME]):
    raise RuntimeError("❌ Missing required MongoDB environment variables.")

mongo_client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
db = mongo_client[DB_NAME]
articles_collection = db[ARTICLES_COLLECTION_NAME]
test_articles_collection = db[TEST_ARTICLES_COLLECTION]
capacities_collection = db[CAPACITIES_COLLECTION]
facilities_collection = db[FACILITIES_COLLECTION]
# MongoDB target collection for Geonames
geonames_collection = db["geonames_lookup"]