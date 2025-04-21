import time
import requests
from bs4 import BeautifulSoup
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pymongo.server_api import ServerApi
import certifi

# Load env vars
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")

# Channel IDs for each tech
tech_channels = {
    'hydropower': 13,
    'nuclear': 14,
    'solar': 15,
    'wind': 16,
    'hydrogen': 17,
    'geothermal': 18,
    'battery': 21,
    'vehicles': 22
}


# MongoDB helpers
def get_mongo_collection(collection_name=None):
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
    db = client[DB_NAME]
    collection_name = collection_name or os.getenv("MONGO_URLS_NAME")
    return db[collection_name]


def get_existing_urls(collection, category):
    return [doc['url'] for doc in collection.find({'category': category}, {'_id': 0, 'url': 1})]


def save_new_urls(collection, urls, category):
    documents = [{'url': url, 'category': category, 'status': 'new'} for url in urls]
    if documents:
        try:
            collection.insert_many(documents, ordered=False)
            print(f"Inserted {len(documents)} new URLs.")
        except Exception as e:
            print("Insert error:", str(e))


# Scrape links from a page
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
    except Exception as e:
        print(f"Failed to scrape {page_url}: {e}")
        return []


# Main crawler
def world_energy_crawler(tech, max_pages):
    print(f'\n--- Starting scrape for {tech} ---')

    category = f"world_energy_{tech}"
    base_url = f'https://www.world-energy.org/channel/{tech_channels[tech]}.html?page='
    all_urls = []

    collection = get_mongo_collection()
    existing_urls = set(get_existing_urls(collection, category))
    print(f"Found {len(existing_urls)} existing URLs for {category} in DB.")

    for page in range(1, max_pages + 1):
        page_url = f'{base_url}{page}'
        print(f'Scraping {page_url}')

        urls = scrape_page(page_url)
        all_urls.extend(urls)
        print(f'Found {len(urls)} URLs on page {page}')
        time.sleep(1)

    all_urls = list(set(all_urls))  # Deduplicate from this run
    print(f'Total unique scraped URLs: {len(all_urls)}')

    new_urls = list(set(all_urls) - existing_urls)
    print(f"New URLs to insert into DB: {len(new_urls)}")

    save_new_urls(collection, new_urls, category)


# Run all techs if script is executed
if __name__ == "__main__":
    for tech in tech_channels.keys():
        world_energy_crawler(tech, max_pages=50)  # You can adjust max_pages as needed
