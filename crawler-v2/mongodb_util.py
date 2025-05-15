import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")

def get_mongo_collection(collection_name=None):
    """Returns the MongoDB collection. Defaults to MONGO_URLS_NAME if not provided."""
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection_name = collection_name or os.getenv("MONGO_URLS_NAME")
    return db[collection_name]

def get_existing_urls(collection, category):
    """Fetch existing URLs from MongoDB collection for a specific category."""
    return [doc['url'] for doc in collection.find({'category': category}, {'_id': 0, 'url': 1})]

def save_new_urls(collection, urls, category):
    """Insert new URLs with a specified category into MongoDB."""
    documents = [{'url': url, 'category': category} for url in urls]
    if documents:
        collection.insert_many(documents, ordered=False)
