# offshorewind_crawler.py

import time
import requests
from bs4 import BeautifulSoup
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
from pymongo.server_api import ServerApi
import logging
logger = logging.getLogger(__name__)

load_dotenv()

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
            logging.info(f"Inserted {len(documents)} new URLs.")
        except Exception as e:
            logging.info("Insert error:", str(e))

base_url = 'https://www.offshorewind.biz/topic/supply-chain/page/'
page_param = ''
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}


def scrape_page(page_url):
    response = requests.get(page_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    urls = [link['href'] for link in soup.find_all('a', href=True) if link['href'].startswith('http')]
    return urls


def offshorewindBiz_crawler(max_pages=150):

    logging.info(f'\n--- Starting crawl for OffshoreWindBiz ---')

    category = 'offshorewind'
    collection = get_mongo_collection()
    existing_urls = set(get_existing_urls(collection, category))
    all_urls = []

    for page in range(1, max_pages + 1):
        page_url = f'{base_url}{page}{page_param}'
        logging.info(f'Scraping {page_url}')

        try:
            urls = scrape_page(page_url)
        except Exception as e:
            logging.info(f"Failed to scrape page {page}: {e}")
            continue
        logging.info(f'Found {len(urls)} URLs on page {page}')
        all_urls.extend(urls)
        logging.info('Crawley read another page ;)')
        time.sleep(1)

    total_scraped = len(all_urls)
    all_urls = list(set(all_urls))
    logging.info(f"Removed {total_scraped - len(all_urls)} duplicate URLs from scraped list.")
    new_urls = list(set(all_urls) - existing_urls)
    logging.info(f"New unique URLs to insert: {len(new_urls)}")
    save_new_urls(collection, new_urls, category)