# crawley_electrive_automobile.py

import os
import re
import time
import certifi

from pymongo.server_api import ServerApi
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
COLLECTION_NAME = os.getenv("MONGO_URLS_NAME")

def get_mongo_collection():
    """Returns the shared MongoDB collection for URLs."""
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
    db = client[DB_NAME]
    return db[COLLECTION_NAME]

def get_existing_urls(collection, category):
    """Fetch existing URLs from MongoDB collection for a specific category."""
    return [doc['url'] for doc in collection.find({'category': category}, {'_id': 0, 'url': 1})]

def save_new_urls(collection, urls, category):
    documents = [{'url': url, 'category': category, 'status': 'new'} for url in urls]
    if documents:
        try:
            collection.insert_many(documents, ordered=False)
            print(f"Inserted {len(documents)} new URLs.")
        except Exception as e:
            print("Insert error:", str(e))

# ==============================
# Crawling Logic
# ==============================

# Configuration settings
BASE_URL = 'https://www.electrive.com/category/'

PAGE_TYPES = {
    'automobile': 'automobile/',
    'battery': 'battery-fuel-cell/'
}

def get_initial_url(page_type):
    return BASE_URL + PAGE_TYPES.get(page_type, 'automobile/')

def setup_driver():
    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    return webdriver.Chrome(service=service)

def scrape_urls(driver, initial_url, max_pages):
    driver.get(initial_url)
    time.sleep(5)
    urls = []
    page_count = 0

    try:
        while page_count < max_pages:
            links = driver.find_elements(By.TAG_NAME, 'a')
            urls.extend([link.get_attribute('href') for link in links if link.get_attribute('href') is not None])

            more_button = driver.find_element(By.CSS_SELECTOR, 'a.input-button.is-style-ghost[rel="next"]')
            driver.execute_script("arguments[0].click();", more_button)

            print('Crawley read another page ;)')
            time.sleep(5)
            page_count += 1
    except Exception as e:
        print("Reached the end or encountered an error:", str(e))

    return list(set(urls))

def filter_urls(urls):
    pattern = r'^https://www\.electrive\.com/\d{4}/\d{2}/\d{2}/.*$'
    return [url for url in urls if re.match(pattern, url)]

def electrive_crawler(page_type, max_pages):
    print(f"Starting crawl for Electrive: {page_type}")

    category = 'electrive'
    collection = get_mongo_collection()  # Single shared collection for all URLs

    driver = setup_driver()
    initial_url = get_initial_url(page_type)
    urls = scrape_urls(driver, initial_url, max_pages=max_pages)

    existing_urls = set(get_existing_urls(collection, category))
    new_urls = set(urls) - existing_urls
    new_filtered_urls = filter_urls(new_urls)

    save_new_urls(collection, new_filtered_urls, category)
    driver.quit()
