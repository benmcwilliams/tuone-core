import requests
import time
import json
import os
import logging
from typing import List, Dict, Any

# Add parent directory to path to import utils
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import CrawlerUtils

logger = logging.getLogger(__name__)

class EnergyTechGraphQLCrawler:
    def __init__(self):
        self.graphql_url = "https://gemenon.graphql.aspire-ebm.com/"
        self.base_url = "https://www.energytech.com"
        self.source_name = "energytech"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        self.query = """
        query getContentStream($limit: Int, $skip: Int) {
        getContentStream(
            input: {
            pagination: { limit: $limit, skip: $skip }
            sort: { field: published, order: desc }
            }
        ) {
            edges {
            node {
                id
                name
                teaser
                published
                publishedDate
                primarySection { name }
                siteContext { path }
                primaryImage { src }   
            }
            }
        }
        }
        """
        self.output_dir = CrawlerUtils.setup_output_dir(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            self.source_name
        )

    def fetch_articles(self, limit=20, skip=0) -> List[Dict[str, Any]]:
        variables = {"limit": limit, "skip": skip}
        payload = {"query": self.query, "variables": variables}
        response = requests.post(self.graphql_url, headers=self.headers, json=payload)
        response.raise_for_status()
        data = response.json()
        print("response data",data)
        edges = data['data']['getContentStream']['edges']
        return [edge['node'] for edge in edges]

    def crawl_all_articles(self, batch_size=20, max_articles=None, sleep_sec=1) -> List[Dict[str, Any]]:
        all_articles = []
        skip = 0
        while True:
            logger.info(f"Fetching articles {skip + 1} to {skip + batch_size}")
            articles = self.fetch_articles(limit=batch_size, skip=skip)
            if not articles:
                break
            for node in articles:
                article = {
                    "id": node['id'],
                    "title": node['name'],
                    "teaser": node['teaser'],
                    "published": node['published'],
                    "publishedDate": node['publishedDate'],
                    "section": node['primarySection']['name'] if node.get('primarySection') else None,
                    "url": self.base_url + node['siteContext']['path'] if node.get('siteContext') and node['siteContext'].get('path') else None,
                    "image": node['primaryImage']['src'] if node.get('primaryImage') else None,
                    "authors": [a['node']['name'] for a in node.get('authors', {}).get('edges', [])]
                }
                all_articles.append(article)
                if max_articles and len(all_articles) >= max_articles:
                    break
            if max_articles and len(all_articles) >= max_articles:
                break
            skip += batch_size
            time.sleep(sleep_sec)
        return all_articles

    def save_articles(self, articles: List[Dict[str, Any]]):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(self.output_dir, f"{self.source_name}_graphql_articles_{timestamp}.json")
        with open(output_file, 'w') as f:
            json.dump(articles, f, indent=2)
        logger.info(f"Saved {len(articles)} articles to {output_file}")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    crawler = EnergyTechGraphQLCrawler()
    articles = crawler.crawl_all_articles(batch_size=20, max_articles=None, sleep_sec=1)
    crawler.save_articles(articles)
    logger.info(f"Total articles fetched: {len(articles)}")

if __name__ == "__main__":
    main() 