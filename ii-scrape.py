import requests
from bs4 import BeautifulSoup
import json
from src.config.config_scrape import HEADERS, COOKIES
from functions.scrape_utils import load_two_digit_ids, load_existing_urls, get_urls_to_scrape, get_date, format_date, extract_date_with_regex

def scrape_article(url: str, article_sequence: int, leading_two_digit: str, file) -> None:
    try:
        response = requests.get(url, headers=HEADERS, cookies=COOKIES)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            title = (soup.select_one('h1') or soup.select_one('h2')).get_text(strip=True) or "No Title Found"
            raw_date = get_date(soup, source)
            print(raw_date)
            date = format_date(raw_date)
            print(date)

            paragraphs = {f"p{idx+1}": p.get_text(strip=True) for idx, p in enumerate(soup.select('p'))}
            article_id = f"{leading_two_digit}{article_sequence:05}"
            article_data = {
                'title': title,
                'paragraphs': paragraphs,
                'meta': {
                    'ID': article_id,
                    'date': date, 
                    'url': url,
                }
            }
            file.write(json.dumps(article_data) + '\n')
            print(title)
        else:
            print(f"Failed to retrieve {url} with status code {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

def scrape_articles(source: str) -> None:
    leading_two_digit = load_two_digit_ids(source)
    urls_to_scrape = get_urls_to_scrape(source)
    print(f"Number of URLs to scrape for {source}: {len(urls_to_scrape)}")

    with open(f'src/database_articles/{source}.jsonl', 'a') as file:
        for article_sequence, url in enumerate(urls_to_scrape, start=len(load_existing_urls(source)) + 1):
            print(f"Scraping article {article_sequence} for source: {source}")
            scrape_article(url, article_sequence, leading_two_digit, file)

def load_sources_from_json(file_path: str) -> list:
    with open(file_path, 'r') as f:
        data = json.load(f)
        return [source['source'] for source in data['sources']]

if __name__ == "__main__":
    # Load sources from the JSON file
    sources = load_sources_from_json('src/source_ID.json')

    for source in sources:
        print(f"Starting to scrape articles for source: {source}")
        scrape_articles(source)
        print(f"Finished scraping articles for source: {source}")