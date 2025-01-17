import json
import os
import pandas as pd
import re
from dateutil import parser
from bs4 import BeautifulSoup
from src.inputs.scrape_date_selectors import DATE_SELECTORS

# Constants
TARGET_FORMAT = "%d-%m-%Y"
JSONL_PATH = 'src/database_articles/'

def load_two_digit_ids(source: str) -> str:
    with open('src/source_ID.json', 'r') as json_file:
        data = json.load(json_file)
        return {item['source']: item['two_digit_ID'] for item in data['sources']}.get(source)

def load_existing_urls(source: str) -> list:
    existing_json = f'{JSONL_PATH}{source}.jsonl'
    if os.path.exists(existing_json):
        with open(existing_json, 'r') as file:
            return [json.loads(line)['meta']['url'] for line in file if line.strip()]
    return []

def get_urls_to_scrape(source: str) -> list:
    file = pd.read_csv(f'src/database_urls/URLs/{source}_urls.csv')
    urls = file['URL'][:25000].to_list()
    existing_urls = load_existing_urls(source)
    return list(set(urls) - set(existing_urls))

def extract_date_with_regex(date_str: str) -> str:
    date_pattern = r"(\d{2}\.\d{2}\.\d{4})"
    date_match = re.search(date_pattern, date_str)
    return date_match.group(1) if date_match else date_str

def get_date(soup: BeautifulSoup, website: str) -> str:
    selector_type, selector = DATE_SELECTORS.get(website, (None, None))
    date_element = (soup.select_one(selector) if selector_type == 'class' 
                    else soup.find(selector) if selector_type == 'tag' 
                    else None)
    
    date = date_element.get_text(strip=True) if date_element else "No Date Found"
    
    # Clean the date string to remove any unwanted text
    # Keep the full date including the year
    if ',' in date:
        date = date.split(',')[0] + ',' + date.split(',')[1]  # Keep the month and day, and the year part
    
    # Remove any trailing text after the date
    date = re.sub(r'\s*by.*$', '', date).strip()  # Remove 'by' and anything after it

    # Ensure the date is in a format that can be parsed
    date = date.strip()  # Remove any leading/trailing whitespace

    # Handle specific cases for websites that may have additional text
    if website in ['electrive', 'electrive_automobile']:
        return extract_date_with_regex(date)
    
    return date

def format_date(date_str: str) -> str:
    if date_str == "No Date Found":
        return None  # Return None for no date found

    try:
        # Parse the date string
        parsed_date = parser.parse(date_str, dayfirst=True)
        # Return the date in the desired format
        return parsed_date.strftime(TARGET_FORMAT)
    except ValueError as e:
        print(f"Error parsing date '{date_str}': {e}")
        return None 