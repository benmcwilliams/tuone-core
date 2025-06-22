import os
import json
from datetime import datetime
from typing import Set, Dict, Any, List
import requests
from bs4 import BeautifulSoup
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CrawlerUtils:
    @staticmethod
    def setup_output_dir(base_dir: str, source_name: str) -> str:
        """
        Create and return the output directory for a specific source
        Args:
            base_dir: Base directory for all data sources
            source_name: Name of the data source
        Returns:
            Path to the output directory
        """
        output_dir = os.path.join(base_dir, source_name, 'data')
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    @staticmethod
    def save_urls_to_file(urls: Set[str], output_dir: str, source_name: str) -> str:
        """
        Save crawled URLs to a JSON file
        Args:
            urls: Set of URLs to save
            output_dir: Directory to save the file
            source_name: Name of the data source
        Returns:
            Path to the saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f'{source_name}_urls_{timestamp}.json')
        
        data = {
            'source': source_name,
            'crawled_at': datetime.now().isoformat(),
            'urls': list(urls)
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(urls)} URLs to {output_file}")
        return output_file

    @staticmethod
    def save_urls_with_source_pages(urls_by_page: Dict[str, Set[str]], output_dir: str, source_name: str) -> str:
        """
        Save crawled URLs with their source page information
        Args:
            urls_by_page: Dictionary mapping page URLs to sets of article URLs
            output_dir: Directory to save the file
            source_name: Name of the data source
        Returns:
            Path to the saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f'{source_name}_urls_with_sources_{timestamp}.json')
        
        # Convert sets to lists for JSON serialization
        data = {
            'source': source_name,
            'crawled_at': datetime.now().isoformat(),
            'urls_by_page': {
                page_url: list(urls) for page_url, urls in urls_by_page.items()
            },
            'total_urls': sum(len(urls) for urls in urls_by_page.values()),
            'total_pages': len(urls_by_page)
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {data['total_urls']} URLs from {data['total_pages']} pages to {output_file}")
        return output_file

    @staticmethod
    def make_request(url: str, headers: Dict[str, str], timeout: int = 30) -> requests.Response:
        """
        Make an HTTP request with error handling
        Args:
            url: URL to request
            headers: HTTP headers
            timeout: Request timeout in seconds
        Returns:
            Response object
        """
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise

    @staticmethod
    def extract_text_from_element(element: BeautifulSoup, selector: str) -> str:
        """
        Safely extract text from a BeautifulSoup element
        Args:
            element: BeautifulSoup element
            selector: CSS selector
        Returns:
            Extracted text or empty string
        """
        try:
            found = element.select_one(selector)
            return found.get_text(strip=True) if found else ""
        except Exception as e:
            logger.error(f"Error extracting text with selector {selector}: {str(e)}")
            return ""

    @staticmethod
    def extract_attribute_from_element(element: BeautifulSoup, selector: str, attribute: str) -> str:
        """
        Safely extract attribute from a BeautifulSoup element
        Args:
            element: BeautifulSoup element
            selector: CSS selector
            attribute: Attribute name to extract
        Returns:
            Attribute value or empty string
        """
        try:
            found = element.select_one(selector)
            return found.get(attribute, "") if found else ""
        except Exception as e:
            logger.error(f"Error extracting attribute {attribute} with selector {selector}: {str(e)}")
            return ""

    @staticmethod
    def rate_limit(seconds: int = 2) -> None:
        """
        Rate limiting function
        Args:
            seconds: Number of seconds to wait
        """
        time.sleep(seconds)

    @staticmethod
    def get_default_headers() -> Dict[str, str]:
        """
        Get default headers for requests
        Returns:
            Dictionary of headers
        """
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate if a URL is properly formatted
        Args:
            url: URL to validate
        Returns:
            True if valid, False otherwise
        """
        try:
            result = requests.utils.urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False 