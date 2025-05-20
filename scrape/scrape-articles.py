import os
import requests
import certifi
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config.config_scrape import HEADERS, COOKIES
from scrap_function.utility import get_date, format_date
from dotenv import load_dotenv
from datetime import datetime, timezone
from requests.exceptions import Timeout, RequestException
import re

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
URLS_COLLECTION_NAME = os.getenv("MONGO_DB_URLS_COLLECTION")
ARTICLES_COLLECTION_NAME = os.getenv("MONGO_DB_ARTICLES_COLLECTION_NAME")

# Initialize MongoDB connection
client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
db = client[DB_NAME]
urls_collection = db[URLS_COLLECTION_NAME]
articles_collection = db[ARTICLES_COLLECTION_NAME]

keywords = {"factory", "facility", "plant", "production line", "production site", "refinery", "pilot project", "energy project",
            "mining project", "dam"}

# Expected date format
date_format = "%d-%m-%Y"


def scrape_article(mongo_doc: dict) -> None:
    url = mongo_doc.get('url')
    doc_id = mongo_doc.get('_id')
    category = mongo_doc.get('category')

    try:
        response = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=30)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            title_tag = soup.select_one('h1') or soup.select_one('h2')
            title = title_tag.get_text(strip=True) if title_tag else "No Title Found"

            raw_date = get_date(soup, category)
            print(f"{title} - Raw date: {raw_date}")
            date = format_date(raw_date)
            print(f"{title} - Formatted date: {date}")

            date_utc = ""
            if date:
                try:
                    date_utc = datetime.strptime(date, date_format).replace(tzinfo=timezone.utc)
                except Exception as e:
                    print(f"[!] Failed to parse date '{date}' using format '{date_format}': {e}")
            else:
                print(f"[!] No valid date found for article: {title}")

            paragraphs_dict = {
                f"p{idx + 1}": p.get_text(strip=True)
                for idx, p in enumerate(soup.select('p'))
            }

            paragraphs = [paragraphs_dict]  # Wrap the dict in a list

            # Check for keywords in title and paragraphs
            title_lower = title.lower()
            all_paragraphs_text = " ".join(paragraphs_dict.values()).lower()

            #regex checking for patterns
            pattern = re.compile(r'\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b', re.IGNORECASE)

            if not (pattern.search(title_lower) or pattern.search(all_paragraphs_text)):
                urls_collection.update_one({'_id': doc_id}, {'$set': {'status': 'irrelevant'}})
                print(f"[–] Skipped (no keywords found): {title}")
                return

            article_data = {
                'title': title,
                'paragraphs': paragraphs,
                'meta': {
                    'date': date_utc,
                    'url': url,
                    'category': category,
                }
            }

            articles_collection.insert_one(article_data)
            urls_collection.update_one({'_id': doc_id}, {'$set': {'status': 'extracted'}})
            print(f"[✓] Scraped and saved: {title}")

        else:
            raise Exception(f"HTTP {response.status_code}")

    except Timeout:
        urls_collection.update_one({'_id': doc_id}, {'$set': {'status': 'timeout'}})
        print(f"[⏰] Timeout while scraping {url} — skipped.")

    except RequestException as req_err:
        urls_collection.update_one({'_id': doc_id}, {'$set': {'status': 'failed', 'error': str(req_err)}})
        print(f"[✗] Request error scraping {url}: {req_err}")

    except Exception as e:
        urls_collection.update_one({'_id': doc_id}, {'$set': {'status': 'failed', 'error': str(e)}})
        print(f"[✗] Failed to scrape {url}: {e}")

def scrape_all_new_articles():
    new_articles_cursor = urls_collection.find({'status': 'new'})
    new_count = urls_collection.count_documents({'status': 'new'})
    print(f"Found {new_count} new articles to scrape.\n")

    for doc in new_articles_cursor:
        print(f"Scraping article: {doc.get('url')}")
        scrape_article(doc)


if __name__ == "__main__":
    print("\n=== Starting full scrape ===\n")
    scrape_all_new_articles()
    print("\n=== Finished scraping ===\n")
