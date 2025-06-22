import requests
from bs4 import BeautifulSoup
from typing import List, Set
from config.config_scrape import HEADERS, COOKIES
import time
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
import certifi

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
URLS_COLLECTION_NAME = os.getenv("MONGO_DB_URLS_COLLECTION")

# Initialize MongoDB connection
client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
db = client[DB_NAME]
urls_collection = db[URLS_COLLECTION_NAME]

def get_article_urls_from_page(url: str) -> Set[str]:
    """
    Extract article URLs from a given page of energytech.com
    """
    article_urls = set()
    try:
        response = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all article links
            # EnergyTech articles are typically in <a> tags with href containing the article path
            article_links = soup.find_all('a', href=True)
            
            for link in article_links:
                href = link['href']
                # Filter for article URLs (they typically contain the date in the path)
                if href.startswith('/') and any(month in href.lower() for month in ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']):
                    full_url = f"https://www.energytech.com{href}"
                    article_urls.add(full_url)
                    
        return article_urls
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return set()

def save_urls_to_mongodb(urls: Set[str]) -> None:
    """
    Save crawled URLs to MongoDB
    """
    for url in urls:
        # Check if URL already exists
        existing_url = urls_collection.find_one({'url': url})
        if not existing_url:
            urls_collection.insert_one({
                'url': url,
                'category': 'energytech',
                'status': 'new',
                'crawled_at': time.time()
            })
            print(f"Added new URL: {url}")
        else:
            print(f"URL already exists: {url}")

def crawl_energytech(max_pages: int = 5) -> Set[str]:
    """
    Crawl energytech.com and collect article URLs
    Args:
        max_pages: Maximum number of pages to crawl
    Returns:
        Set of article URLs
    """
    all_article_urls = set()
    base_url = "https://www.energytech.com"
    
    # Start with the main page
    current_page = 1
    while current_page <= max_pages:
        page_url = f"{base_url}/page/{current_page}" if current_page > 1 else base_url
        print(f"Crawling page {current_page}: {page_url}")
        
        page_urls = get_article_urls_from_page(page_url)
        if not page_urls:
            print(f"No more articles found on page {current_page}")
            break
            
        all_article_urls.update(page_urls)
        print(f"Found {len(page_urls)} articles on page {current_page}")
        
        # Be nice to the server
        time.sleep(2)
        current_page += 1
    
    # Save URLs to MongoDB
    save_urls_to_mongodb(all_article_urls)
    return all_article_urls

if __name__ == "__main__":
    # Test the crawler
    urls = crawl_energytech(max_pages=3)
    print(f"\nTotal unique articles found: {len(urls)}")
    for url in urls:
        print(url) 