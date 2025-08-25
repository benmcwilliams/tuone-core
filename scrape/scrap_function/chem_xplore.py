import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import Optional, Dict, Any


def extract_chemxplore_article(url: str) -> Optional[Dict[str, Any]]:
    """
    Extract article content from a ChemXplore article.
    Returns structured dict with paragraphs as { p1, p2, ... }.
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
    }

    try:
        # Fetch page
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # --- Title ---
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "No Title Found"

        # --- Date ---
        date_tag = soup.find("div", class_="article__date")
        date_str = date_tag.get_text(strip=True) if date_tag else None

        date_utc = datetime.utcnow().replace(tzinfo=timezone.utc)  # fallback
        if date_str:
            try:
                # Example: "Apr 4, 2025"
                parsed = datetime.strptime(date_str, "%b %d, %Y")
                date_utc = parsed.replace(tzinfo=timezone.utc)
            except Exception:
                # If parsing fails, keep fallback UTC now
                pass

        # --- Author ---
        author_tag = soup.find("div", class_="article__author")
        author = author_tag.get_text(strip=True) if author_tag else "Unknown"

        # --- Category ---
        category_tag = soup.find("div", class_="article__category")
        category = category_tag.get_text(strip=True) if category_tag else "chemxplore"

        # --- Paragraphs ---
        raw_paragraphs = []
        article_content = soup.select_one("div.article__content") or soup.select_one("article")

        if article_content:
            for element in article_content.find_all(["p", "h2", "h3"]):
                text = element.get_text(" ", strip=True)
                if text and len(text) > 5:
                    raw_paragraphs.append(text)

        if not raw_paragraphs:
            for p in soup.find_all("p"):
                text = p.get_text(" ", strip=True)
                if text and len(text) > 10:
                    raw_paragraphs.append(text)

        # Convert to { p1, p2, ... }
        paragraph_obj = {f"p{i+1}": text for i, text in enumerate(raw_paragraphs)}
        paragraphs = [paragraph_obj]  # ✅ matches Biomass/EnergyTech format

        # --- Final dict ---
        return {
            "title": title,
            "paragraphs": paragraphs,
            "meta": {
                "date": date_utc,
                "url": url,
                "category": category,
                "author": author,
                "source": "chemxplore",
            },
        }

    except Exception as e:
        print(f"❌ ChemXplore scraper failed for {url}: {e}")
        return None
