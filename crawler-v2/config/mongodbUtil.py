from pymongo import MongoClient

def get_mongo_collection(collection_name):
    client = MongoClient("mongodb://localhost:27017")  # Adjust URI if needed
    db = client['electrive_scraper']
    return db[collection_name]

def get_existing_urls(collection):
    return [doc['url'] for doc in collection.find({}, {'_id': 0, 'url': 1})]

def save_new_urls(collection, urls):
    documents = [{'url': url} for url in urls]
    if documents:
        collection.insert_many(documents)