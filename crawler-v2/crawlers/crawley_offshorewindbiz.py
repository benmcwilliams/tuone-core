import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from src.database_urls.utils import get_unique_elements, save_urls_to_csv  # Importing from utils

OUTPUT_CSV_PATH = 'src/database_urls/URLs/offshoreWindBiz_urls.csv'
base_url = 'https://www.offshorewind.biz/topic/supply-chain/page/'
page_param = ''

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

def scrape_page(page_url):
    response = requests.get(page_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    urls = [link['href'] for link in soup.find_all('a', href=True) if link['href'].startswith('http')]
    return urls

def offshorewindBiz_crawler(max_pages=150):

    print('Starting scrape for offshore wind...')
    
    try:
        existing_urls = pd.read_csv(OUTPUT_CSV_PATH)['URL'].tolist()
    except FileNotFoundError:
        existing_urls = []

    all_urls = []  # List to hold all scraped URLs

    for page in range(1, max_pages + 1):  # Adjust the range as needed
        page_url = f'{base_url}{page}{page_param}'
        print(f'Scraping {page_url}')
        
        urls = scrape_page(page_url)
        all_urls.extend(urls)  # Add the found URLs to the all_urls list
        print(f'Found {len(urls)} URLs on page {page}')
        print('Crawley read another page ;)')
        time.sleep(1)

    # Optionally, remove duplicates
    all_urls = list(set(all_urls))

    new_urls = get_unique_elements(all_urls, existing_urls)
    urls_to_write = existing_urls + new_urls
    print(f"Total URLs to write: {len(urls_to_write)}")

    # Save the URLs to a CSV file
    save_urls_to_csv(urls_to_write, OUTPUT_CSV_PATH)