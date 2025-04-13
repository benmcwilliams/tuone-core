# crawley_electrive_automobile.py

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from src.database_urls.utils import get_unique_elements, save_urls_to_csv  # Importing from utils

# Configuration settings
BASE_URL = 'https://www.electrive.com/category/'

# Define page types
PAGE_TYPES = {
    'automobile': 'automobile/',
    'battery': 'battery-fuel-cell/'
}

def get_initial_url(page_type):
    """Returns the initial URL based on the page type."""
    return BASE_URL + PAGE_TYPES.get(page_type, 'automobile/')  # Default to automobile if not found

def setup_driver():
    """Sets up the Selenium WebDriver."""
    driver_path = ChromeDriverManager().install()  # Automatically installs the ChromeDriver
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service)
    return driver

def scrape_urls(driver, initial_url, max_pages):
    """Scrapes URLs from the specified initial URL up to a maximum number of pages."""
    driver.get(initial_url)
    time.sleep(5)  # Wait for the page to load
    urls = []
    page_count = 0  # Initialize page counter

    try:
        while page_count < max_pages:  # Check against max_pages
            links = driver.find_elements(By.TAG_NAME, 'a')
            urls.extend([link.get_attribute('href') for link in links if link.get_attribute('href') is not None])
            
            more_button = driver.find_element(By.CSS_SELECTOR, 'a.input-button.is-style-ghost[rel="next"]')
            driver.execute_script("arguments[0].click();", more_button)

            print('Crawley read another page ;)')
            time.sleep(5)  # Wait for the new content to load
            
            page_count += 1  # Increment page counter
            
    except Exception as e:
        print("Reached the end of the pages or encountered an error:", str(e))

    return list(set(urls))  # Remove duplicates

def filter_urls(urls):
    """Filters and returns only the URLs that match the specified pattern."""
    pattern = r'^https://www\.electrive\.com/\d{4}/\d{2}/\d{2}/.*$'
    return [url for url in urls if re.match(pattern, url)]

def electrive_crawler(page_type, max_pages):
    """Main function to execute the web scraping and URL filtering."""
    
    print(f"Starting crawl for Electrive, {page_type}...")
    
    # Dynamically set the CSV file path based on the page type
    CSV_FILE_PATH = f'src/database_urls/URLs/electrive_{page_type}_urls.csv'
    
    driver = setup_driver()
    
    initial_url = get_initial_url(page_type)  # Get the initial URL based on the page type
    urls = scrape_urls(driver, initial_url, max_pages=max_pages)
    
    existing_urls = pd.read_csv(CSV_FILE_PATH)['URL'].to_list()
    new_urls = get_unique_elements(urls, existing_urls)
    new_filtered_urls = filter_urls(new_urls)
    
    urls_to_write = existing_urls + new_filtered_urls
    save_urls_to_csv(urls_to_write, CSV_FILE_PATH)
    
    driver.quit()  # Clean up