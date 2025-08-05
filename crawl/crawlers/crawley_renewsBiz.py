import time
import requests
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
from pymongo.server_api import ServerApi
import logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")

headers = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    ),
    'Accept': (
        'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,'
        'image/webp,image/apng,*/*;q=0.8'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

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
            logging.info(f"Inserted {len(documents)} new URLs.")
        except Exception as e:
            logging.info("Insert error:", str(e))


def scrape_page(page_url, prepend_url, headers=None):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,  # Make it a visible browser window
                args=["--start-maximized"]
            )
            context = browser.new_context(
                user_agent=headers["User-Agent"],
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()
            page.goto(page_url, timeout=60000)

            # Add a delay to mimic human behavior
            page.wait_for_timeout(5000)

            # Continue as usual
            html = page.content()

            # optional dump for inspection
            # with open("debug_renews.html", "w", encoding="utf-8") as f:
            #     f.write(html)

            browser.close()

            soup = BeautifulSoup(html, 'html.parser')
            urls = [
                prepend_url + a['href']
                for article in soup.find_all('article')
                for a in article.find_all('a', href=True)
            ]
            return urls
    except Exception as e:
        logging.info(f"Error scraping {page_url}: {e}")
        return []

# Main crawler
def renews_biz_crawler(tech, max_pages):
    logging.info(f'\n--- Starting crawl for {tech} (renewsBiz) ---')

    tech_dict = {
        'offshore-wind': 'offshore_wind',
        'onshore-wind': 'onshore_wind',
        'solar': 'solar'
    }

    category = f"renewsBiz"
    base_url = f'https://renews.biz/{tech}/?p='
    prepend_url = 'https://renews.biz'
    all_urls = []

    collection = get_mongo_collection()
    existing_urls = set(get_existing_urls(collection, category))
    logging.info(f"Found {len(existing_urls)} existing URLs in DB for {category}.")

    for page in range(1, max_pages + 1):
        page_url = f'{base_url}{page}'
        logging.info(f'Scraping {page_url}')

        urls = scrape_page(page_url, prepend_url, headers)
        all_urls.extend(urls)
        logging.info(f'Found {len(urls)} URLs on page {page}')
        logging.info('Crawley read another page ;)')
        time.sleep(1)

    all_urls = list(set(all_urls))  # Deduplicate from current scrape
    logging.info(f'Total unique URLs found: {len(all_urls)}')

    new_urls = list(set(all_urls) - existing_urls)
    logging.info(f"New URLs to insert: {len(new_urls)}")

    save_new_urls(collection, new_urls, category)


# Entry point
if __name__ == "__main__":
    tech_list = ['offshore-wind', 'onshore-wind', 'solar']
    for tech in tech_list:
        logging.info(f'\n--- Starting scrape for {tech} ---')
        renews_biz_crawler(tech, max_pages=352)
