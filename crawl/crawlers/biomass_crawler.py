import requests
from bs4 import BeautifulSoup
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
from pymongo.server_api import ServerApi
import time
import random

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
COLLECTION_NAME = os.getenv("MONGO_DB_URLS_COLLECTION_NAME")


def get_mongo_collection():
    """Connect once to MongoDB and return collection handle."""
    client = MongoClient(
        MONGO_URI,
        server_api=ServerApi("1"),
        tlsCAFile=certifi.where()
    )
    db = client[DB_NAME]
    return db[COLLECTION_NAME]


def get_existing_urls(collection, category):
    """Get already stored URLs for a category to avoid duplicates."""
    return [
        doc["url"]
        for doc in collection.find(
            {"category": category},
            {"_id": 0, "url": 1}
        )
    ]


def save_new_urls(collection, urls, category):
    """Insert new URLs into MongoDB."""
    documents = [
        {"url": url, "category": category, "status": "new"}
        for url in urls
    ]
    if documents:
        try:
            collection.insert_many(documents, ordered=False)
            print(f"✅ Inserted {len(documents)} new URLs.")
        except Exception as e:
            print("❌ Insert error:", str(e))


def safe_get(url, retries=3, base_delay=5):
    """Fetch a page with retries and exponential backoff."""
    for attempt in range(retries):
        try:
            print(f"🔍 Fetching: {url} (Attempt {attempt + 1}/{retries})")
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20
            )
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout:
            wait = base_delay * (2 ** attempt) + random.uniform(0, 2)
            print(f"⏳ Timeout on {url}, retrying in {wait:.1f}s...")
            time.sleep(wait)
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None
    print(f"🚨 Giving up on {url} after {retries} attempts.")
    return None


def fetch_urls_from_page(page_url, base_url="https://biomassmagazine.com"):
    """Scrapes one page of Biomass Magazine Advanced Biofuels articles."""
    resp = safe_get(page_url)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    article_links = soup.select("p.chakra-text.css-bnnz7e a.chakra-link.css-spn4bz")

    urls = []
    for link in article_links:
        href = link.get("href")
        if href:
            # Convert relative URLs to absolute
            full_url = base_url + href if href.startswith("/") else href
            urls.append(full_url)

    print(f"📰 Found {len(urls)} article URLs on this page.")
    return urls


def biomass_crawler(start_page=1, end_page=5):
    """Crawl multiple pages of biomassmagazine.com for Advanced Biofuels articles."""
    category = "biomass-advanced-biofuels"
    collection = get_mongo_collection()

    print(f"🚀 Starting crawler for category: {category}")
    existing_urls = set(get_existing_urls(collection, category))

    all_new_urls = []

    for page in range(start_page, end_page + 1):
        page_url = f"https://biomassmagazine.com/tag/advanced-biofuels/{page}"
        urls = fetch_urls_from_page(page_url)

        # Filter out already-stored URLs
        new_urls = list(set(urls) - existing_urls)
        all_new_urls.extend(new_urls)

        # Polite randomized delay (3–7s)
        sleep_time = random.uniform(3, 7)
        print(f"😴 Sleeping {sleep_time:.1f}s before next page...")
        time.sleep(sleep_time)

    print(f"🔎 Total new URLs to insert: {len(all_new_urls)}")
    save_new_urls(collection, all_new_urls, category)
