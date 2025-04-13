import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from src.database_urls.utils import save_urls_to_csv, get_unique_elements

OUTPUT_CSV_PATH = 'src/database_urls/URLs/pv_tech_urls.csv'

def scrape_page(page_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(page_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    urls = [link['href'] for link in soup.find_all('a', href=True) if link['href'].startswith('http')]
    return urls

def pv_tech_crawler(max_pages=1):
    
    print('Starting scrape for PV Tech...')

    all_urls = []

    # Read existing URLs from the CSV file if it exists
    try:
        existing_urls = pd.read_csv(OUTPUT_CSV_PATH)['URL'].tolist()
    except FileNotFoundError:
        existing_urls = []

    for page in range(1, max_pages + 1):  # Use max_pages parameter
        page_url = f'https://www.pv-tech.org/category/news/page/{page}/'
        print(f'Scraping {page_url}')
        
        urls = scrape_page(page_url)
        all_urls.extend(urls)  # Add the found URLs to the all_urls list
        print(f'Found {len(urls)} URLs on page {page}')
        time.sleep(1)

    # Get unique URLs
    all_urls = list(set(all_urls))
    print(f'Total unique URLs found: {len(all_urls)}')

    # Identify new URLs
    new_urls = get_unique_elements(all_urls, existing_urls)
    urls_to_write = existing_urls + new_urls
    print(f"Total URLs to write: {len(urls_to_write)}")

    # Save all URLs back to the CSV file
    save_urls_to_csv(urls_to_write, OUTPUT_CSV_PATH)