import os
import requests
import certifi
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config.config_scrape import HEADERS, COOKIES
from scrap_function.utility import get_date, format_date,extract_article_text_energy_tech
from dotenv import load_dotenv
from datetime import datetime, timezone
from requests.exceptions import Timeout, RequestException
from dateutil import parser
import re
from boiler_markers import BOILER_STRINGS

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
            "mining project", "dam", "wind farm", "solar farm", "solar park", "BESS project", "start of construction",
            "close the plant"}

subsidy_keywords = {"subsidy", "subsidies", "aid", "funding"}

# dropped battery & lithium & geothermal

# Expected date format
date_format = "%d-%m-%Y"

def scrape_article(mongo_doc: dict) -> None:
    url = mongo_doc.get('url')
    doc_id = mongo_doc.get('_id')
    category = mongo_doc.get('category')

    try:
        if category == "energytech":
            print("[⚡] Using GraphQL scraper for EnergyTech article")

            article_info = extract_article_text_energy_tech(url)
            if not article_info or "paragraphs" not in article_info:
                raise Exception("Failed to extract article content for EnergyTech")

            title = article_info.get("title", "EnergyTech Article")
            raw_date = article_info.get("date", "")
            paragraphs = article_info["paragraphs"]

            # Convert raw date string (if any) to datetime object
            date_utc = ""
            if raw_date:
                try:
                    date_utc = datetime.fromtimestamp(int(raw_date) / 1000, tz=timezone.utc)
                except Exception as e:
                    print(f"[!] Failed to parse EnergyTech timestamp '{raw_date}': {e}")
            else:
                date_utc = datetime.utcnow().replace(tzinfo=timezone.utc)

        else:
            print("[🌐] Using default scraper")
            response = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=30)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")

            soup = BeautifulSoup(response.content, 'html.parser')

            # Title tag
            title_tag = soup.select_one('h1') or soup.select_one('h2')
            title = title_tag.get_text(strip=True) if title_tag else "No Title Found"

            # Date tag
            raw_date = get_date(soup, category)
            print("raw date",raw_date)

            def get_utc_date_from_raw(raw_date: str) -> datetime:
                if not raw_date or raw_date == "No Date Found":
                    return datetime.utcnow().replace(tzinfo=timezone.utc)

                try:
                    if raw_date.isdigit():
                        timestamp_sec = int(raw_date) / 1000
                        return datetime.fromtimestamp(timestamp_sec, tz=timezone.utc)
                    parsed = parser.parse(raw_date, dayfirst=True)
                    return parsed.replace(tzinfo=timezone.utc)

                except Exception as e:
                    print(f"[!] Failed to parse raw date '{raw_date}': {e}")
                    return datetime.utcnow().replace(tzinfo=timezone.utc)

            date_utc = get_utc_date_from_raw(raw_date)

            clean_paras = []
            for p in soup.select('p'):
                txt = p.get_text(strip=True)
                if txt in BOILER_STRINGS:
                    continue
                clean_paras.append(txt)

            paragraphs_dict = {
                f"p{idx + 1}": txt
                for idx, txt in enumerate(clean_paras)
            }
            paragraphs = [paragraphs_dict]

        # Keyword filtering
        single_word = {k for k in keywords if ' ' not in k}
        multi_word = {k for k in keywords if ' ' in k}

        word_regex = re.compile(r'\b(' + '|'.join(re.escape(k) for k in single_word) + r')\b', re.IGNORECASE)
        title_txt = title.lower()
        body_txt = " ".join(paragraphs[0].values()).lower()

        found = (
            word_regex.search(title_txt) or
            word_regex.search(body_txt) or
            any(k in title_txt or k in body_txt for k in multi_word)
        )

        subsidy_found = any(
            k in title_txt or k in body_txt
            for k in subsidy_keywords
        )

        if not found:
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
                'subsidy': subsidy_found
            }
        }

        articles_collection.insert_one(article_data)
        urls_collection.update_one({'_id': doc_id}, {'$set': {'status': 'extracted'}})
        print(f"[✓] Scraped and saved: {title}")

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
