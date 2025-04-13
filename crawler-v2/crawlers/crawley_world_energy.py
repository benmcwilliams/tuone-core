import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from src.database_urls.utils import save_urls_to_csv, get_unique_elements

# Define output CSV file paths for each technology
OUTPUT_CSV_PATHS = {
    'hydropower': 'src/database_urls/URLs/world_energy_hydropower_urls.csv',
    'nuclear': 'src/database_urls/URLs/world_energy_nuclear_urls.csv',
    'solar': 'src/database_urls/URLs/world_energy_solar_urls.csv',
    'wind': 'src/database_urls/URLs/world_energy_wind_urls.csv',
    'hydrogen': 'src/database_urls/URLs/world_energy_hydrogen_urls.csv',
    'geothermal': 'src/database_urls/URLs/world_energy_geothermal_urls.csv',
    'battery': 'src/database_urls/URLs/world_energy_battery_urls.csv',
    'vehicles': 'src/database_urls/URLs/world_energy_vehicles_urls.csv'
}

tech_channels = {
    'hydropower': 13,
    'nuclear': 14,
    'solar': 15,
    'wind': 16,
    'hydrogen': 17,
    'geothermal': 18,
    'battery': 21,
    'vehicles': 22
}

def get_unique_elements(list_a, list_b):
    return [item for item in list_a if item not in list_b]

def scrape_page(page_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(page_url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    urls = [link['href'] for link in soup.find_all('a', href=True) if link['href'].startswith('http')]
    return urls

def world_energy_crawler(tech, max_pages):
    # Update urls_collection based on the technology
    print(f'Starting scrape for {tech}...')

    urls_collection = f'1_crawley/URLs/world_energy_{tech}_urls.csv'
    base_url = f'https://www.world-energy.org/channel/{tech_channels[tech]}.html?page='
    all_urls = []

    # Read existing URLs from the CSV file if it exists
    try:
        existing_urls = pd.read_csv(OUTPUT_CSV_PATHS[tech])['URL'].tolist()
    except FileNotFoundError:
        existing_urls = []
    
    for page in range(1, max_pages + 1):
        page_url = f'{base_url}{page}'
        print(f'Scraping {page_url}')
        urls = scrape_page(page_url)
        all_urls.extend(urls)
        print(f'Found {len(urls)} URLs on page {page}')
        time.sleep(1)

    all_urls = list(set(all_urls))
    print(f'Total unique URLs found for {tech}: {len(all_urls)}')

    # Identify new URLs
    new_urls = get_unique_elements(all_urls, existing_urls)
    urls_to_write = existing_urls + new_urls
    print(f"Total URLs to write: {len(urls_to_write)}")

    # Save all URLs back to the CSV file
    save_urls_to_csv(urls_to_write, OUTPUT_CSV_PATHS[tech])

    return all_urls