import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from src.database_urls.utils import get_unique_elements, save_urls_to_csv  # Importing the utility scrap_function
import re  # Importing regex for filtering

# Define headers for the requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

def scrape_page(page_url):
    try:
        response = requests.get(page_url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')
        urls = [link['href'] for link in soup.find_all('a', href=True) if link['href'].startswith('http')]
        return urls
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")  # Log the error
        return []  # Return an empty list if the page is not found
    except Exception as e:
        print(f"An error occurred: {e}")  # Log any other errors
        return []  # Return an empty list for any other exceptions

def pv_magazine_crawler(page_extensions, tech='manufacturing', max_pages=200):
    
    print(f'Starting scrape for PV Magazine, {tech}...')

    all_urls = []

    # Read existing URLs from the CSV file if it exists
    output_csv_path = f'src/database_urls/URLs/pv_magazine_{tech}_urls.csv'  # Define the output path based on tech
    try:
        existing_urls = pd.read_csv(output_csv_path)['URL'].tolist()
    except FileNotFoundError:
        existing_urls = []

    for page in range(1, max_pages + 1):
        page_url = f'https://www.pv-magazine.com/category/{page_extensions[tech]}/page/{page}/'
        print(f'Scraping {page_url}')
        
        urls = scrape_page(page_url)
        if not urls:  # If no URLs were found, exit the loop
            print(f"No URLs found on page {page}. Exiting the scrape.")
            break
        
        all_urls.extend(urls)  # Add the found URLs to the all_urls list
        print(f'Found {len(urls)} URLs on page {page}')
        print('Crawley read another page ;)')
        time.sleep(1)

    # Filter out URLs that end with #respond
    filtered_urls = [url for url in all_urls if not re.search(r'#respond$', url)]
    print(f'Total URLs after filtering: {len(filtered_urls)}')

    # Get unique URLs
    unique_urls = list(set(filtered_urls))
    print(f'Total unique URLs found: {len(unique_urls)}')

    # Identify new URLs
    new_urls = get_unique_elements(unique_urls, existing_urls)
    urls_to_write = existing_urls + new_urls
    print(f"Total URLs to write: {len(urls_to_write)}")

    # Save all URLs back to the CSV file
    save_urls_to_csv(urls_to_write, output_csv_path)

# This allows the function to be called from crawl.py
if __name__ == "__main__":
    page_extensions = {
        "hydrogen": "hydrogen",
        "manufacturing": "manufacturing/modules-upstream-manufacturing"
    }
    scrape_pv_magazine(page_extensions)