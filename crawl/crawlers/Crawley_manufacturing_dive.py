# manufacturing_dive_crawler.py

import requests
from bs4 import BeautifulSoup
import time
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
from pymongo.server_api import ServerApi

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
COLLECTION_NAME = os.getenv("MONGO_DB_URLS_COLLECTION_NAME")


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
            print(f"✅ Inserted {len(documents)} new URLs into MongoDB.")
        except Exception as e:
            print("❌ Insert error:", str(e))


def scrape_manufacturing_dive_articles(base_url="https://www.manufacturingdive.com/topic/openings-expansions/", max_pages=None):
    """
    Scrape article URLs from Manufacturing Dive (Openings & Expansions)
    """
    all_article_urls = []
    page_num = 1

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"🚀 Starting to scrape Manufacturing Dive articles from: {base_url}")

    while True:
        page_url = base_url if page_num == 1 else f"{base_url}?page={page_num}"
        print(f"\n📄 Scraping page {page_num}: {page_url}")

        try:
            response = requests.get(page_url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract articles
            articles = soup.find_all("h3", class_="feed__title")

            if not articles:
                print(f"⚠️ No articles found on page {page_num}, stopping.")
                break

            page_article_urls = []
            for article in articles:
                a_tag = article.find("a")
                if not a_tag or "href" not in a_tag.attrs:
                    continue
                href = a_tag["href"]
                if href.startswith("/"):
                    href = "https://www.manufacturingdive.com" + href
                if href not in all_article_urls:
                    page_article_urls.append(href)

            all_article_urls.extend(page_article_urls)
            print(f"📝 Added {len(page_article_urls)} unique article URLs from page {page_num}")
            print(f"📊 Total so far: {len(all_article_urls)}")

            # Stop if max_pages is reached
            if max_pages and page_num >= max_pages:
                print(f"✅ Reached maximum page limit ({max_pages})")
                break

            # Check if next page exists (simple check: look for "next" link)
            next_button = soup.find("a", {"class": "button", "rel": "next"})
            if not next_button:
                print(f"✅ No more pages after page {page_num}")
                break

            page_num += 1
            time.sleep(1)  # polite delay

        except requests.exceptions.RequestException as e:
            print(f"❌ Network error scraping page {page_num}: {e}")
            break
        except Exception as e:
            print(f"❌ Unexpected error on page {page_num}: {e}")
            break

    print(f"\n🏁 Scraping completed! Total {len(all_article_urls)} articles found.")
    return all_article_urls


def manufacturing_dive_crawler(max_pages=5):
    """Main function: scrape Manufacturing Dive and store in MongoDB"""
    category = "manufacturing-dive-news"
    collection = get_mongo_collection()

    existing_urls = set(get_existing_urls(collection, category))
    scraped_urls = scrape_manufacturing_dive_articles(max_pages=max_pages)

    new_urls = list(set(scraped_urls) - existing_urls)
    print(f"\n🔎 New URLs to insert: {len(new_urls)}")
    save_new_urls(collection, new_urls, category)
