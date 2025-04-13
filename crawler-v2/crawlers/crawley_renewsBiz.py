import time
import requests
from bs4 import BeautifulSoup
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
from pymongo.server_api import ServerApi

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
    """Insert new URLs with category into MongoDB"""
    documents = [{'url': url, 'category': category} for url in urls]
    if documents:
        collection.insert_many(documents, ordered=False)
        print(f"Inserted {len(documents)} new URLs into MongoDB.")


# Page-level scraping
def scrape_page(page_url, prepend_url, headers):
    try:
        response = requests.get(page_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        urls = [prepend_url + article.find('a')['href'] for article in soup.find_all('article') if article.find('a')]
        return urls
    except Exception as e:
        print(f"Error scraping {page_url}: {e}")
        return []


# Main crawler
def renews_biz_crawler(tech, max_pages):
    print(f'Starting scrape for {tech} in renewsBiz...')

    tech_dict = {
        'offshore-wind': 'offshore_wind',
        'onshore-wind': 'onshore_wind',
        'solar': 'solar'
    }

    category = f"renews_{tech_dict[tech]}"
    base_url = f'https://renews.biz/{tech}/?p='
    prepend_url = 'https://renews.biz'
    all_urls = []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    collection = get_mongo_collection()
    existing_urls = set(get_existing_urls(collection, category))
    print(f"Found {len(existing_urls)} existing URLs in DB for {category}.")

    for page in range(1, max_pages + 1):
        page_url = f'{base_url}{page}'
        print(f'Scraping {page_url}')

        urls = scrape_page(page_url, prepend_url, headers)
        all_urls.extend(urls)
        print(f'Found {len(urls)} URLs on page {page}')
        print('Crawley read another page ;)')
        time.sleep(1)

    all_urls = list(set(all_urls))  # Deduplicate from current scrape
    print(f'Total unique URLs found: {len(all_urls)}')

    new_urls = list(set(all_urls) - existing_urls)
    print(f"New URLs to insert: {len(new_urls)}")

    save_new_urls(collection, new_urls, category)


# Entry point
if __name__ == "__main__":
    tech_list = ['offshore-wind', 'onshore-wind', 'solar']
    for tech in tech_list:
        print(f'\n--- Starting scrape for {tech} ---')
        renews_biz_crawler(tech, max_pages=352)
