import os
import requests
import certifi
import logging
from bs4 import BeautifulSoup
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config.config_scrape import HEADERS, COOKIES
from scrap_function.utility import get_date, format_date, extract_article_text_energy_tech
from dotenv import load_dotenv
from datetime import datetime, timezone
from requests.exceptions import Timeout, RequestException
from dateutil import parser
from scrap_function.biomass_scrapper import extract_biomass_article_paragraphs
from scrap_function.chem_xplore import extract_chemxplore_article
from scrap_function.manufacturing_dive import extract_manufacturing_dive_article
import re

# ------------------ Logging Setup ------------------
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for very detailed logs
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()  # You can also add FileHandler if you want logs saved
    ]
)
logger = logging.getLogger(__name__)
# ----------------------------------------------------

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGO_DB_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_DB_URLS_COLLECTION_NAME = os.getenv("MONGO_DB_URLS_COLLECTION_NAME")
MONGO_DB_ARTICLES_COLLECTION_NAME = os.getenv("MONGO_DB_ARTICLES_COLLECTION_NAME")

# Initialize MongoDB connection
client = MongoClient(MONGO_DB_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
db = client[MONGO_DB_NAME]
urls_collection = db[MONGO_DB_URLS_COLLECTION_NAME]
articles_collection = db[MONGO_DB_ARTICLES_COLLECTION_NAME]

keywords = {
    "factory", "facility", "plant", "production line", "production site", "refinery",
    "pilot project", "energy project", "mining project", "dam", "wind farm", "solar farm",
    "solar park", "BESS project", "geothermal", "battery", "lithium"
}


def scrape_article(mongo_doc: dict) -> None:
    url = mongo_doc.get('url')
    doc_id = mongo_doc.get('_id')
    category = mongo_doc.get('category')

    logger.info(f"Scraping started for URL: {url} | Category: {category}")

    try:
        if category == "energytech":
            logger.info("[⚡] Using GraphQL scraper for EnergyTech article")
            article_info = extract_article_text_energy_tech(url)

            if not article_info or "paragraphs" not in article_info:
                raise Exception("Failed to extract article content for EnergyTech")

            title = article_info.get("title", "EnergyTech Article")
            raw_date = article_info.get("date", "")
            paragraphs = article_info["paragraphs"]

            date_utc = ""
            if raw_date:
                try:
                    date_utc = datetime.fromtimestamp(int(raw_date) / 1000, tz=timezone.utc)
                except Exception as e:
                    logger.warning(f"Failed to parse EnergyTech timestamp '{raw_date}': {e}")
            else:
                date_utc = datetime.utcnow().replace(tzinfo=timezone.utc)

            meta = {
                "date": date_utc,
                "url": url,
                "category": category,
                "source": "energytech"
            }

            article_info = {
                "title": title,
                "paragraphs": paragraphs,
                "meta": meta,
            }

        elif category == "biomass":
            logger.info("[🌱] Using Biomass scraper")
            article_info = extract_biomass_article_paragraphs(url)

        elif category == "chemxplore-news":
            logger.info("[🧪] Using ChemXplore scraper")
            article_info = extract_chemxplore_article(url)

        elif category == "manufacturing-dive-news":
            logger.info("[🏭] Using Manufacturing Dive scraper")
            article_info = extract_manufacturing_dive_article(url)

        else:
            logger.info("[🌐] Using default scraper")
            response = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=30)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")

            soup = BeautifulSoup(response.content, 'html.parser')

            # Title
            title_tag = soup.select_one('h1') or soup.select_one('h2')
            title = title_tag.get_text(strip=True) if title_tag else "No Title Found"

            # Date
            raw_date = get_date(soup, category)
            logger.debug(f"Raw date extracted: {raw_date}")

            def get_utc_date_from_raw(raw_date: str) -> datetime:
                if not raw_date or raw_date == "No Date Found":
                    return datetime.utcnow().replace(tzinfo=timezone.utc)
                try:
                    if raw_date.isdigit():
                        return datetime.fromtimestamp(int(raw_date)/1000, tz=timezone.utc)
                    parsed = parser.parse(raw_date, dayfirst=True)
                    return parsed.replace(tzinfo=timezone.utc)
                except Exception as e:
                    logger.warning(f"Failed to parse raw date '{raw_date}': {e}")
                    return datetime.utcnow().replace(tzinfo=timezone.utc)

            date_utc = get_utc_date_from_raw(raw_date)

            paragraphs_dict = {
                f"p{idx + 1}": p.get_text(strip=True)
                for idx, p in enumerate(soup.select('p'))
            }

            article_info = {
                "title": title,
                "paragraphs": [paragraphs_dict],
                "meta": {
                    "date": date_utc,
                    "url": url,
                    "category": category,
                    "source": "default_scraper"
                }
            }

        # 🚨 Common validation
        if not article_info or "paragraphs" not in article_info:
            raise Exception(f"Failed to extract article content for {category}")

        title = article_info.get("title", "Untitled Article")
        paragraphs = article_info["paragraphs"]
        meta = article_info["meta"]

        # ✅ Keyword filtering
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

        if not found:
            urls_collection.update_one({'_id': doc_id}, {'$set': {'status': 'irrelevant'}})
            logger.info(f"[–] Skipped (no keywords found): {title}")
            return

        # ✅ Save to DB
        articles_collection.insert_one({
            "title": title,
            "paragraphs": paragraphs,
            "meta": meta,
        })
        urls_collection.update_one({'_id': doc_id}, {'$set': {'status': 'extracted'}})
        logger.info(f"[✓] Scraped and saved: {title}")

    except Timeout:
        urls_collection.update_one({'_id': doc_id}, {'$set': {'status': 'timeout'}})
        logger.error(f"[⏰] Timeout while scraping {url} — skipped.")

    except RequestException as req_err:
        urls_collection.update_one({'_id': doc_id}, {'$set': {'status': 'failed', 'error': str(req_err)}})
        logger.error(f"[✗] Request error scraping {url}: {req_err}")

    except Exception as e:
        urls_collection.update_one({'_id': doc_id}, {'$set': {'status': 'failed', 'error': str(e)}})
        logger.exception(f"[✗] Failed to scrape {url}: {e}")

def main():
    logger.info("Starting scrape-articles.py")

    # Fetch documents to scrape
    docs_to_scrape = urls_collection.find({"status": {"$nin": ["extracted", "irrelevant"]}})

    count = 0
    for doc in docs_to_scrape:
        scrape_article(doc)
        count += 1

    logger.info(f"Scraping completed. Total articles processed: {count}")


if __name__ == "__main__":
    main()