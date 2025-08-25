import requests
from bs4 import BeautifulSoup
import json
import html
from datetime import datetime, timezone
from dateutil import parser
from typing import Optional, Dict, Any


def extract_biomass_article_paragraphs(url: str) -> Optional[Dict[str, Any]]:
    """Extract paragraphs from a Biomass Magazine article"""

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Biomass uses Next.js JSON data in script tag
        script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if not script_tag:
            print("❌ No article data found in script tag")
            return None

        json_data = json.loads(script_tag.string)
        article = json_data.get("props", {}).get("pageProps", {}).get("article", {})

        title = article.get("title", "No title found")
        body_html = article.get("body", "")
        published_at = article.get("publishedAt")  # e.g. "2024-08-15T12:00:00Z"
        author = article.get("author", {}).get("name", "Unknown")
        summary = article.get("summary", "")

        # Normalize date
        if published_at:
            try:
                date_utc = parser.parse(published_at).astimezone(timezone.utc)
            except Exception:
                date_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        else:
            date_utc = datetime.utcnow().replace(tzinfo=timezone.utc)

        # Parse article body
        decoded_body = html.unescape(body_html)
        body_soup = BeautifulSoup(decoded_body, "html.parser")
        paragraph_nodes = body_soup.find_all("p")

        paragraphs = {
            f"p{idx+1}": p.get_text(" ", strip=True)
            for idx, p in enumerate(paragraph_nodes)
            if p.get_text(strip=True)
        }

        return {
            "title": title,
            "paragraphs": [paragraphs],  # ✅ consistent format
            "meta": {
                "date": date_utc,
                "url": url,
                "author": author,
                "summary": summary,
                "source": "biomass_magazine",
            },
        }

    except Exception as e:
        print(f"❌ Biomass scraper failed: {e}")
        return None
