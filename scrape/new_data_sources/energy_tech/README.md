# EnergyTech Crawler

This crawler extracts article URLs from EnergyTech.com's search page and saves them to JSON files.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the crawler:
```bash
python crawler.py
```

## Features

- Crawls EnergyTech.com's search page and extracts article URLs
- Automatically detects and handles pagination
- Saves URLs to timestamped JSON files in the `data` directory
- Includes rate limiting to be respectful to the server
- Filters URLs to ensure they are actual articles

## Output

The crawler creates JSON files in the `data` directory with the following structure:
```json
{
  "source": "energytech",
  "crawled_at": "2024-03-21T10:30:00",
  "urls": [
    "https://www.energytech.com/article1",
    "https://www.energytech.com/article2",
    ...
  ]
}
```

## Configuration

You can modify the following parameters in the code:
- `max_pages`: Number of pages to crawl (default: None, which means crawl all pages)
- `time.sleep()`: Delay between requests (default: 2 seconds)

## How it Works

1. Starts from the search page (https://www.energytech.com/search)
2. Detects the total number of pages from the pagination
3. Iterates through each page, collecting article URLs
4. Saves all unique URLs to a JSON file 