import requests
from bs4 import BeautifulSoup
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
from pymongo.server_api import ServerApi
import time

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
COLLECTION_NAME = os.getenv("MONGO_DB_URLS_COLLECTION_NAME")


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
            print(f"✅ Inserted {len(documents)} new URLs.")
        except Exception as e:
            print("❌ Insert error:", str(e))


def fetch_urls_from_page(page_url, base_url="https://biomassmagazine.com"):
    """Scrapes one page of Biomass Magazine Advanced Biofuels articles."""
    try:
        print(f"🔍 Fetching page: {page_url}")
        resp = requests.get(
            page_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        article_links = soup.select("p.chakra-text.css-bnnz7e a.chakra-link.css-spn4bz")

        urls = []
        for link in article_links:
            href = link.get("href")
            if href:
                # Convert relative URLs to absolute
                if href.startswith("/"):
                    full_url = base_url + href
                else:
                    full_url = href
                urls.append(full_url)

        print(f"📰 Found {len(urls)} article URLs on this page.")
        return urls

    except Exception as e:
        print(f"❌ Failed to fetch {page_url}: {e}")
        return []


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

        # Be polite (avoid hammering the site)
        time.sleep(2)

    print(f"🔎 Total new URLs to insert: {len(all_new_urls)}")
    save_new_urls(collection, all_new_urls, category)