import os
import requests
import certifi
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config.config_scrape import HEADERS, COOKIES
from scrap_function.utility import get_date, format_date
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB config
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
URLS_COLLECTION_NAME = os.getenv("MONGO_URLS_NAME")
ARTICLES_COLLECTION_NAME = os.getenv("MONGO_DB_ARTICLES_COLLECTION_NAME")

# Connect to MongoDB
client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
db = client[DB_NAME]
urls_collection = db[URLS_COLLECTION_NAME]
articles_collection = db[ARTICLES_COLLECTION_NAME]


def scrape_article(mongo_doc: dict) -> None:
    url = mongo_doc['url']
    doc_id = mongo_doc['_id']
    category = mongo_doc['category']

    try:
        response = requests.get(url, headers=HEADERS, cookies=COOKIES)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            title_tag = soup.select_one('h1') or soup.select_one('h2')
            title = title_tag.get_text(strip=True) if title_tag else "No Title Found"

            raw_date = get_date(soup,category)
            date = format_date(raw_date)

            paragraphs = {
                f"p{idx + 1}": p.get_text(strip=True)
                for idx, p in enumerate(soup.select('p'))
            }

            article_data = {
                'title': title,
                'paragraphs': paragraphs,
                'meta': {
                    'date': date,
                    'url': url,
                }
            }

            articles_collection.insert_one(article_data)
            urls_collection.update_one({'_id': doc_id}, {'$set': {'status': 'extracted'}})
            print(f"[✓] Scraped and saved: {title}")
        else:
            raise Exception(f"HTTP {response.status_code}")

    except Exception as e:
        urls_collection.update_one({'_id': doc_id}, {'$set': {'status': 'failed', 'error': str(e)}})
        print(f"[✗] Failed to scrape {url}: {e}")


def scrape_all_new_articles():
    cursor = urls_collection.find({'status': 'new'})
    count = urls_collection.count_documents({'status': 'new'})
    print(f"Found {count} new articles to scrape.")

    for doc in cursor:
        print(f"Scraping article: {doc['url']}")
        scrape_article(doc)


if __name__ == "__main__":
    print("\n=== Starting full scrape ===")
    scrape_all_new_articles()
    print("=== Finished scraping ===\n")
