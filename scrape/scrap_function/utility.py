import re
from dateutil import parser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

url = "https://gemenon.graphql.aspire-ebm.com/"
base_url = "https://www.energytech.com"

headers = {
    "host": "gemenon.graphql.aspire-ebm.com",
    "connection": "keep-alive",
    "sec-ch-ua-platform": "\"Linux\"",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
    "content-type": "application/json",
    "sec-ch-ua-mobile": "?0",
    "x-tenant-key": "ebm_energytech",
    "accept": "*/*",
    "origin": "https://www.energytech.com",
    "sec-fetch-site": "cross-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://www.energytech.com/",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9"
}

# Constants
TARGET_FORMAT = "%d-%m-%Y"

DATE_SELECTORS = {
    'electrive': ('class', '.date'),
    'energy_voice_hydrogen': ('class', '.post-timestamp__published'),
    'offshorewind': ('class', '.article-meta__info'),
    'powertechnology': ('class', '.article-meta .date-published'),
    'pvmagazine': ('class', '.entry-published.updated'),
    'pvtech': ('tag', 'time'),
    'renewsBiz': ('class', '.first-upper[itemprop="dateCreated"]'),
    'world_energy': ('class', '.color-front.fwb')
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

def extract_article_text_energy_tech(full_article_url):
    alias_path = urlparse(full_article_url).path
    payload = {
        "query": "query getWebsiteLayoutPage($alias: String!, $useCache: Boolean, $preview: Boolean, $cacheKey: String) {\n  getWebsiteLayoutPage(\n    input: { alias: $alias, useCache: $useCache, preview: $preview, cacheKey: $cacheKey }\n  ) {\n    id\n    name\n    module\n    type\n    alias\n    contentTypes\n    pageType\n    isGlobal\n    tenants\n    propagate\n    hideHeader\n    hideFooter\n    key\n    loadMoreType {\n      type\n    }\n    primaryGrid\n    secondaryGrid\n    excludeAds {\n      welcomeAd\n      headerLeaderboardAd\n      stickyLeaderboardAd\n      contentBodyNativeAd\n      contentBodyEmbedAd\n      contentListNativeAd\n      reskinAd\n    }\n    pageData\n    cache\n    created\n    usedContentIds\n    usedIssueIds\n  }\n}",
        "variables": {
            "alias": alias_path,
            "cacheKey": "v2.8",
            "preview": False,
            "useCache": True
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        body_blocks = (
            result.get("data", {})
            .get("getWebsiteLayoutPage", {})
            .get("pageData", {})
            .get("bodyBlocks", [])
        )
        # Extract and combine all HTML text blocks
        html_blocks = [
            block["settings"]["text"]
            for block in body_blocks
            if block.get("settings", {}).get("text")
        ]
        combined_html = "\n".join(html_blocks)
        soup = BeautifulSoup(combined_html, "html.parser")
        paragraphs_dict = {
            f"p{idx + 1}": p.get_text(strip=True)
            for idx, p in enumerate(soup.select("p"))
        }
        paragraphs = [paragraphs_dict]
        return {
            "paragraphs": paragraphs,
            "date": result.get("data", {}).get("getWebsiteLayoutPage", {}).get("pageData", {}).get("published"),
            "title": result.get("data", {}).get("getWebsiteLayoutPage", {}).get("pageData", {}).get("name"),
        }
    except requests.RequestException as e:
        print("Request failed:", e)
    except Exception as e:
        print("Error parsing article:", e)

    return None
