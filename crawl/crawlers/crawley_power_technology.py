# crawley_power_technology.py
from pymongo.server_api import ServerApi
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import time
import certifi
import logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
COLLECTION_NAME = os.getenv("MONGO_URLS_NAME")

# MongoDB Utilities
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
            logging.info("Insert error:", str(e))

# Main Crawler
def power_technology_crawler(max_pages=10):
    logging.info(f'\n--- Starting crawl for Power Technology ---')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    initial_url = 'https://www.power-technology.com/news/?cf-view'
    driver.get(initial_url)

    urls = []
    page_count = 0

    try:
        while page_count < max_pages:
            links = driver.find_elements(By.TAG_NAME, 'a')
            urls.extend([link.get_attribute('href') for link in links if link.get_attribute('href') is not None])

            try:
                view_more_button = driver.find_element(By.ID, "pagination_showmore_category_btn")
                actions = ActionChains(driver)
                actions.move_to_element(view_more_button).perform()
                view_more_button.click()
            except Exception as e:
                logging.info("No more pages to click or error occurred:", str(e))
                break

            logging.info(f'Crawley read page {page_count + 1} ;)')
            page_count += 1
            time.sleep(5)
    except Exception as e:
        logging.info("Encountered an error while scraping:", str(e))
    finally:
        driver.quit()

    # Deduplicate and save to MongoDB
    total_scraped = len(urls)
    urls = list(set(urls))  # Remove duplicates
    logging.info(f"Removed {total_scraped - len(urls)} duplicate URLs from scraped list.")

    category = 'powertechnology'
    collection = get_mongo_collection()
    existing_urls = set(get_existing_urls(collection, category))
    new_urls = list(set(urls) - existing_urls)

    logging.info(f"New unique URLs to insert: {len(new_urls)}")
    save_new_urls(collection, new_urls, category)

if __name__ == "__main__":
    power_technology_crawler()
