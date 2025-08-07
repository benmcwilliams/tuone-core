import time
import requests
from bs4 import BeautifulSoup
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pymongo.server_api import ServerApi
import certifi
import logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")


# MongoDB helpers
def get_mongo_collection(collection_name=None):
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
    db = client[DB_NAME]
    collection_name = collection_name or os.getenv("MONGO_URLS_NAME")
    return db[collection_name]


def get_existing_urls(collection, category):
    """Fetch URLs from MongoDB for a specific category"""
    return [doc['url'] for doc in collection.find({'category': category}, {'_id': 0, 'url': 1})]


def save_new_urls(collection, urls, category):
    documents = [{'url': url, 'category': category, 'status': 'new'} for url in urls]
    if documents:
        try:
            collection.insert_many(documents, ordered=False)
            logging.info(f"✅ Inserted {len(documents)} new URLs.")
        except Exception as e:
            logging.info("Insert error:", str(e))


# Scraper logic
def scrape_page(page_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.get(page_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        urls = [link['href'] for link in soup.find_all('a', href=True) if link['href'].startswith('http')]
        return urls
    except requests.exceptions.RequestException as e:
        logging.info(f"Request failed for {page_url}: {e}")
        return []


def pv_tech_crawler(max_pages=1):
    logging.info(f'\n--- Starting crawl for PV Tech ---')

    category = "pvtech"
    collection = get_mongo_collection()
    all_urls = []

    for page in range(1, max_pages + 1):
        page_url = f'https://www.pv-tech.org/category/news/page/{page}/'
        logging.info(f'Scraping {page_url}')

        urls = scrape_page(page_url)
        all_urls.extend(urls)
        logging.info(f'Found {len(urls)} URLs on page {page}')
        logging.info('Crawley read another page ;)')
        time.sleep(1)

    # Deduplicate from current scrape
    unique_urls = list(set(all_urls))
    logging.info(f'Total unique URLs found: {len(unique_urls)}')

    existing_urls = set(get_existing_urls(collection, category))
    logging.info(f"Found {len(existing_urls)} existing URLs in the DB.")

    new_urls = list(set(unique_urls) - existing_urls)
    logging.info(f"New URLs to insert: {len(new_urls)}")

    save_new_urls(collection, new_urls, category)


# For testing or running directly
if __name__ == "__main__":
    pv_tech_crawler(max_pages=10)
