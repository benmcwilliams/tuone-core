from datetime import datetime, timezone
from typing import Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
from dateutil import parser


def extract_manufacturing_dive_article(url: str) -> Optional[Dict[str, Any]]:
    """
    Extract paragraphs from a Manufacturing Dive article in the same structure as Biomass scraper
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # --- Extract Title ---
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "No title found"

        # --- Date ---
        date_tag = soup.select_one("time")
        raw_date = date_tag.get("datetime") if date_tag else None

        if raw_date:
            try:
                date_utc = parser.parse(raw_date).astimezone(timezone.utc)
            except Exception:
                date_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        else:
            date_utc = datetime.utcnow().replace(tzinfo=timezone.utc)

        # --- Author ---
        author_tag = soup.select_one(".byline__author") or soup.select_one(".author-name")
        author = author_tag.get_text(strip=True) if author_tag else "Unknown"

        # --- Category ---
        category_tag = soup.select_one(".article-category") or soup.select_one(".topic")
        category = category_tag.get_text(strip=True) if category_tag else "Unknown"

        # --- Paragraphs ---
        paragraphs = {}
        content_area = soup.select_one(".article-body") or soup.select_one("article")
        if content_area:
            for idx, element in enumerate(content_area.find_all("p")):
                text = element.get_text(strip=True)
                if text and len(text) > 10:
                    paragraphs[f"p{idx+1}"] = text

        if not paragraphs:
            # fallback to all <p> tags
            for idx, p in enumerate(soup.find_all("p")):
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    paragraphs[f"p{idx+1}"] = text

        return {
            "title": title,
            "paragraphs": [paragraphs],  # ✅ same as Biomass scraper
            "meta": {
                "date": date_utc,
                "url": url,
                "author": author,
                "category": category,
                "source": "manufacturing_dive"
            }
        }

    except Exception as e:
        print(f"❌ Manufacturing Dive scraper failed: {e}")
        return None
