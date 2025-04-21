import re
from dateutil import parser
from bs4 import BeautifulSoup

# Constants
TARGET_FORMAT = "%d-%m-%Y"

DATE_SELECTORS = {
    'electrive': ('class', '.date'),
    'energy_voice_hydrogen': ('class', '.post-timestamp__published'),
    'offshorewind': ('class', '.article-meta__info'),
    'powertechnology': ('class', '.article-meta .date-published'),
    'pvmagazine': ('class', '.entry-published.updated'),
    'pvtech': ('tag', 'time'),
    'renewsBiz_offshore_wind': ('class', '.first-upper[itemprop="dateCreated"]'),
    'renewsBiz_onshore_wind': ('class', '.first-upper[itemprop="dateCreated"]'),
    'renewsBiz_solar': ('class', '.first-upper[itemprop="dateCreated"]'),
    'world_energy_battery': ('class', '.color-front.fwb'),
    'world_energy_hydrogen': ('class', '.color-front.fwb'),
    'world_energy_solar': ('class', '.color-front.fwb'),
    'world_energy_wind': ('class', '.color-front.fwb'),
    'world_energy_geothermal': ('class', '.color-front.fwb'),
    'world_energy_hydropower': ('class', '.color-front.fwb'),
    'world_energy_nuclear': ('class', '.color-front.fwb'),
    'world_energy_vehicles': ('class', '.color-front.fwb')
}


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

    if ',' in date:
        date = date.split(',')[0] + ',' + date.split(',')[1]  # Keep the month and day, and the year part
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