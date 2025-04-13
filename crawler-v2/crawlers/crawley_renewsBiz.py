import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from src.database_urls.utils import get_unique_elements, save_urls_to_csv  # Importing from utils

# Define the CSV file path at the top for clarity
CSV_FILE_PATH_TEMPLATE = 'src/database_urls/URLs/renewsBiz_{}_urls.csv'

tech_dict = {
    'offshore-wind': 'offshore_wind',
    'onshore-wind': 'onshore_wind',
    'solar': 'solar'
}

def renews_biz_crawler(tech, max_pages):

    print(f'Starting scrape for {tech} in renewsBiz...')

    base_url = f'https://renews.biz/{tech}/?p='
    prepend_url = 'https://renews.biz'
    all_urls = []

    # Read existing URLs from the CSV file if it exists
    try:
        existing_urls = pd.read_csv(CSV_FILE_PATH_TEMPLATE.format(tech))['URL'].tolist()
    except FileNotFoundError:
        existing_urls = []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    def scrape_page(page_url):
        response = requests.get(page_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        urls = [prepend_url + article.find('a')['href'] for article in soup.find_all('article') if article.find('a')]
        return urls

    for page in range(1, max_pages + 1):
        page_url = f'{base_url}{page}'
        print(f'Scraping {page_url}')
        
        urls = scrape_page(page_url)
        all_urls.extend(urls)
        print(f'Found {len(urls)} URLs on page {page}')
        print('Crawley read another page ;)')
        time.sleep(1)

    # Optionally, remove duplicates
    all_urls = list(set(all_urls))
    
    # Identify new URLs
    new_urls = get_unique_elements(all_urls, existing_urls)
    urls_to_write = existing_urls + new_urls
    print(f"Total URLs to write: {len(urls_to_write)}")

    # Save all URLs back to the CSV file
    save_urls_to_csv(urls_to_write, CSV_FILE_PATH_TEMPLATE.format(tech_dict[tech]))

if __name__ == "__main__":
    for tech in tech_dict.keys():
        print(f'Starting scrape for {tech}...')
        scrape_renews_biz(tech, max_pages=352)