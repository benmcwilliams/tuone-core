import time
import requests
from bs4 import BeautifulSoup
import re
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

# Headers for requests
headers = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    ),
    'Accept': (
        'text/html,application/xhtml+xml,application/xml;q=0.9,'
        'image/avif,image/webp,image/apng,*/*;q=0.8'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
}

# MongoDB helpers
def get_mongo_collection(collection_name=None):
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
    db = client[DB_NAME]
    collection_name = collection_name or os.getenv("MONGO_URLS_NAME")
    return db[collection_name]

def get_existing_urls(collection, category):
    """Fetch URLs from the DB for a specific category"""
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

    try:
        logger.debug(f"Requesting URL: {page_url} with headers: {headers}")
        response = requests.get(page_url, headers=headers)
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        response.raise_for_status()

        # optional debugging (PRINT PAGE)
        # with open("pv_magazine_debug.html", "w", encoding="utf-8") as f:
        #     f.write(response.text)

        soup = BeautifulSoup(response.text, 'html.parser')
        urls = [link['href'] for link in soup.find_all('a', href=True) if link['href'].startswith('http')]
        return urls
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}, response: {getattr(e.response, 'text', '')[:50]}")
        return []
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return []

def pv_magazine_crawler(page_extensions, tech='manufacturing', max_pages=200):
    logging.info(f'\n--- Starting crawl for {tech} (PV Magazine) ---')

    category = "pvmagazine"
    collection = get_mongo_collection()

    all_urls = []

    for page in range(1, max_pages + 1):
        page_url = f'https://www.pv-magazine.com/category/{page_extensions[tech]}/page/{page}/'
        logging.info(f'Scraping {page_url}')

        urls = scrape_page(page_url)
        if not urls:
            logging.info(f"No URLs found on page {page}. Exiting early.")
            break

        all_urls.extend(urls)
        logging.info(f"Found {len(urls)} URLs on page {page}")
        logging.info('Crawley read another page ;)')
        time.sleep(1)

    # Filter out unwanted URLs
    all_urls_len = len(all_urls)
    logging.info(f"Before filtering, {all_urls_len} length.")
    filtered_urls = [url for url in all_urls if not re.search(r'#respond$', url)]
    logging.info(f"Total URLs after filtering: {len(filtered_urls)}")

    # Deduplicate
    unique_urls = list(set(filtered_urls))
    logging.info(f"Total unique URLs found: {len(unique_urls)}")

    existing_urls = set(get_existing_urls(collection, category))
    logging.info(f"Found {len(existing_urls)} existing URLs in the DB.")

    new_urls = list(set(unique_urls) - existing_urls)
    logging.info(f"New URLs to insert: {len(new_urls)}")

    # Save to MongoDB
    save_new_urls(collection, new_urls, category)

# Entry point
if __name__ == "__main__":
    page_extensions = {
        "hydrogen": "hydrogen",
        "manufacturing": "manufacturing/modules-upstream-manufacturing"
    }
    pv_magazine_crawler(page_extensions)