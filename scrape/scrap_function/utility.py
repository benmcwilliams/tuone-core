import re
import json
from dateutil import parser
import requests
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime, timezone

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

# Patterns to skip non–main-text paragraphs (source lines, image captions, tag lines)
_SOURCE_LINE_RE = re.compile(r"^Source\s*:\s*.+")
_IMAGE_CAPTION_RE = re.compile(r"^Image\s*(?:source)?\s*:\s*.+", re.IGNORECASE)
_TAG_LINE_RE = re.compile(r"^#[\w\s#]+$")


def should_skip_paragraph(txt: str) -> bool:
    """Return True if paragraph looks like a source line, image caption, or tag line."""
    if not txt or not txt.strip():
        return True
    if _SOURCE_LINE_RE.match(txt):
        return True
    if _IMAGE_CAPTION_RE.match(txt):
        return True
    if _TAG_LINE_RE.match(txt.strip()):
        return True
    return False

DATE_SELECTORS = {
    'electrive': ('class', '.date'),
    'energy_voice_hydrogen': ('class', '.post-timestamp__published'),
    'offshorewind': ('class', '.article-meta__info'),
    'powertechnology': ('class', '.article-meta .date-published'),
    'pvmagazine': ('class', '.entry-published.updated'),
    'pvtech': ('tag', 'time'),
    'renewsBiz': ('class', '.first-upper[itemprop="dateCreated"]'),
    'world_energy': ('class', '.color-front.fwb'),
    'justauto': ('class', 'div.article-meta > span.date-published'),
    'battery-news':('class','li.wpr-post-info-date > span:nth-of-type(2)'),
    'glass-international':('class','li.wpr-post-info-date > span:nth-of-type(2)')
}

def parse_date(date_str):
    date_str = re.sub(r'(\d{1,2})(st|nd|rd|th)', r'\1', date_str)
    formats = [
        "%B %d, %Y",
        "%d %B %Y",
        "%Y-%m-%d",
        "%d. %B %Y",
        "%d %B, %Y",
    ]

    for fmt in formats:
        try:
            print(f'Parsing date that is {datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")}')
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    return date_str

def glass_international_date_util(soup: BeautifulSoup) -> str:
    print(f'Parsing glass international date')
    published_tag = soup.select_one("div.publishedby p")
    text = published_tag.get_text(strip=True) if published_tag else ""
    match = re.search(r"Published (\d{1,2}(?:st|nd|rd|th)? [A-Za-z]+, \d{4})", text)
    date_raw = match.group(1) if match else "No date found"
    print("Raw date in the crawler function",date_raw)
    return parse_date(date_raw)

def battery_news_date_util(soup: BeautifulSoup) -> str:
    date_tag = soup.select_one("li.wpr-post-info-date > span:nth-of-type(2)")
    date_raw = date_tag.get_text(strip=True) if date_tag else "No date found"
    return parse_date(date_raw)


def transformers_magazine_date_util(soup: BeautifulSoup) -> str:
    """Extract date from span.post-meta (e.g. 'Europe | November 23, 2021')."""
    meta_tag = soup.select_one("span.post-meta")
    text = meta_tag.get_text(strip=True) if meta_tag else ""
    # Take part after last pipe, or match "Month DD, YYYY"
    if "|" in text:
        text = text.split("|")[-1].strip()
    match = re.search(r"([A-Za-z]+\s+\d{1,2},?\s+\d{4})", text)
    date_raw = match.group(1) if match else (text or "No date found")
    return parse_date(date_raw)


def extract_date_with_regex(date_str: str) -> str:
    date_pattern = r"(\d{2}\.\d{2}\.\d{4})"
    date_match = re.search(date_pattern, date_str)
    return date_match.group(1) if date_match else date_str

def get_date(soup: BeautifulSoup, website: str) -> str:
    print(f"Getting date from {website}")
    if website == "battery_news":
        return battery_news_date_util(soup)
    elif website == "glass-international":
        print("Using glass international date")
        return glass_international_date_util(soup)
    elif website == "transformers-magazine":
        return transformers_magazine_date_util(soup)

    selector_type, selector = DATE_SELECTORS.get(website, (None, None))

    if selector_type == 'class':
        date_element = soup.select_one(selector)
    elif selector_type == 'tag':
        date_element = soup.find(selector)
    else:
        date_element = None

    date = date_element.get_text(strip=True) if date_element else "No Date Found"

    if ',' in date:
        date = date.split(',')[0] + ',' + date.split(',')[1]
    date = re.sub(r'\s*by.*$', '', date).strip()

    if website in ['electrive', 'electrive_automobile']:
        return extract_date_with_regex(date)

    return date


def format_date(date_str: str) -> str:
    if date_str == "No Date Found":
        return None
    try:
        parsed_date = parser.parse(date_str, dayfirst=True)
        return parsed_date.strftime(TARGET_FORMAT)
    except ValueError as e:
        print(f"⚠️ Error parsing date '{date_str}': {e}")
        return None


def _parse_datetime_to_utc(value: str):
    """Parse a datetime string and return UTC datetime, else None."""
    if not value or not isinstance(value, str):
        return None
    try:
        dt = parser.parse(value)
    except Exception:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _extract_confident_publication_date(soup: BeautifulSoup, html: str):
    """
    Enrichment-only publication date rule:
    1) article:published_time
    2) <time datetime="...">
    3) JSON-LD datePublished
    Returns UTC datetime or None when not confident.
    """
    # 1) High-confidence machine-readable meta published time
    meta_candidates = [
        ("property", "article:published_time"),
        ("name", "article:published_time"),
    ]
    for attr, key in meta_candidates:
        tag = soup.find("meta", attrs={attr: key})
        if tag and tag.get("content"):
            dt = _parse_datetime_to_utc(tag.get("content"))
            if dt is not None:
                return dt

    # 2) time datetime tag
    time_tag = soup.find("time")
    if time_tag and time_tag.get("datetime"):
        dt = _parse_datetime_to_utc(time_tag.get("datetime"))
        if dt is not None:
            return dt

    # 3) JSON-LD datePublished
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text() or ""
        if not raw.strip():
            continue
        try:
            parsed_json = json.loads(raw)
        except Exception:
            continue

        def walk(obj):
            if isinstance(obj, dict):
                if "datePublished" in obj:
                    dt = _parse_datetime_to_utc(str(obj.get("datePublished")))
                    if dt is not None:
                        return dt
                for v in obj.values():
                    got = walk(v)
                    if got is not None:
                        return got
            elif isinstance(obj, list):
                for i in obj:
                    got = walk(i)
                    if got is not None:
                        return got
            return None

        got = walk(parsed_json)
        if got is not None:
            return got

    return None


def extract_article_text_enrichment(full_article_url, headers_override=None, cookies_override=None, min_chars=200):
    """
    Extract enrichment article text using a readability-style parser (trafilatura).
    Returns dict(title, paragraphs, date) or None.
    - date is UTC datetime when confident, else None.
    """
    response = requests.get(
        full_article_url,
        headers=headers_override or {},
        cookies=cookies_override or {},
        timeout=30,
    )
    response.raise_for_status()
    html = response.text

    extracted_text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        output_format="txt",
    )
    if not extracted_text or len(extracted_text.strip()) < min_chars:
        return None

    metadata = trafilatura.extract_metadata(html)
    title = (metadata.title if metadata and metadata.title else None)

    soup = BeautifulSoup(html, "html.parser")
    if not title:
        h1 = soup.select_one("h1")
        title = h1.get_text(strip=True) if h1 else "No Title Found"

    date_utc = _extract_confident_publication_date(soup, html)

    lines = [ln.strip() for ln in extracted_text.splitlines() if ln and ln.strip()]
    if not lines:
        return None

    paragraphs = [{
        f"p{idx + 1}": txt
        for idx, txt in enumerate(lines)
    }]

    return {
        "paragraphs": paragraphs,
        "date": date_utc,  # None when not confidently found
        "title": title,
    }


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
