# crawley_power_technology.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
import time
import pandas as pd
from src.database_urls.utils import get_unique_elements, save_urls_to_csv  # Importing scrap_function

# Define the CSV file path
CSV_FILE_PATH = 'src/database_urls/URLs/power_technology_urls.csv'

def power_technology_crawler(max_pages=10):

    print('Starting scrape for Power Technology...')
    
    """Main function to execute the web scraping for Power Technology."""
    # Setup Selenium WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    # Specify the initial URL of the website
    initial_url = 'https://www.power-technology.com/news/?cf-view'

    # Navigate to the initial URL
    driver.get(initial_url)

    urls = []
    page_count = 0  # Initialize page counter

    try:
        while page_count < max_pages:  # Check against max_pages
            # Find all <a> tags on the page and extract the URLs
            links = driver.find_elements(By.TAG_NAME, 'a')
            urls.extend([link.get_attribute('href') for link in links if link.get_attribute('href') is not None])
            
            # Find the "View More" button
            view_more_button = driver.find_element(By.ID, "pagination_showmore_category_btn")

            # Scroll into view and click
            actions = ActionChains(driver)
            actions.move_to_element(view_more_button).perform()
            view_more_button.click()

            print('Crawley read another page ;)')
            print(len(urls))
            page_count += 1  # Increment page counter
            # Wait for the new content to load
            time.sleep(5)
            
    except Exception as e:
        print("Reached the end of the pages or encountered an error:", str(e))

    finally:
        # Clean up
        driver.quit()

        # Read existing URLs from the CSV file
        existing_urls = []
        try:
            existing_urls = pd.read_csv(CSV_FILE_PATH)['URL'].to_list()
            print(f"Found {len(existing_urls)} existing URLs")
        except FileNotFoundError:
            print(f"No existing CSV found at {CSV_FILE_PATH}. Starting fresh.")

        # Remove duplicates using the utility function
        all_urls = get_unique_elements(urls, existing_urls)

        # Identify new URLs
        new_urls = get_unique_elements(all_urls, existing_urls)
        urls_to_write = existing_urls + new_urls
        print(f"Total URLs to write: {len(urls_to_write)}")

        # Save all URLs back to the CSV file using the utility function
        save_urls_to_csv(urls_to_write, CSV_FILE_PATH)

if __name__ == "__main__":
    crawl_power_technology()