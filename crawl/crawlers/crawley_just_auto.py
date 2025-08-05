# justauto_crawler.py

import requests
import xml.etree.ElementTree as ET
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
from pymongo.server_api import ServerApi

# Load environment variables
load_dotenv()

import logging
logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
COLLECTION_NAME = os.getenv("MONGO_URLS_NAME")


def get_mongo_collection():
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
    db = client[DB_NAME]
    return db[COLLECTION_NAME]


def get_existing_urls(collection, category):
    return [doc['url'] for doc in collection.find({'category': category}, {'_id': 0, 'url': 1})]


def save_new_urls(collection, urls, category):
    documents = [{'url': url, 'category': category, 'status': 'new'} for url in urls]
    if documents:
        try:
            collection.insert_many(documents, ordered=False)
            logging.info(f"✅ Inserted {len(documents)} new URLs.")
        except Exception as e:
            logging.info("❌ Insert error:", str(e))


def fetch_urls_from_sitemap(sitemap_url):
    try:
        logging.info(f"🔍 Fetching sitemap: {sitemap_url}")
        response = requests.get(sitemap_url)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        url_tags = root.findall('ns:url', namespace)

        urls = []
        for url_tag in url_tags:
            loc = url_tag.find('ns:loc', namespace)
            if loc is not None and loc.text:
                urls.append(loc.text)

        logging.info(f"📰 Found {len(urls)} article URLs.")
        return urls

    except requests.RequestException as e:
        logging.info(f"❌ Request failed: {e}")
        return []
    except ET.ParseError as e:
        logging.info(f"❌ XML parsing failed: {e}")
        return []


def just_auto_crawler():
    category = "justauto"
    sitemap_url = "https://www.just-auto.com/post-sitemap.xml"
    collection = get_mongo_collection()

    logging.info(f"🚀 Starting crawler for category: {category}")
    existing_urls = set(get_existing_urls(collection, category))

    sitemap_urls = fetch_urls_from_sitemap(sitemap_url)
    new_urls = list(set(sitemap_urls) - existing_urls)

    logging.info(f"🔎 New URLs to insert: {len(new_urls)}")
    save_new_urls(collection, new_urls, category)

