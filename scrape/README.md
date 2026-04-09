# Scrape

Article scraping and text extraction pipeline for URLs stored in MongoDB.

This module reads URLs marked as `status: "new"` in the URLs collection, extracts article content (title, paragraphs, date), and writes normalized article documents to the articles collection.

## What it does

- **Input:** URL documents in MongoDB (typically produced by `crawl/`) with `status: "new"`.
- **Output:** Article documents inserted into the articles collection.
- **Status updates:** URL records are updated to `extracted`, `irrelevant`, `timeout`, or `failed`.
- **Filtering:** Non-enrichment categories are keyword-filtered to reduce irrelevant content.

## Structure

| Path | Role |
|------|------|
| `scrape-articles.py` | Main entry point. Scrapes URLs, extracts content, writes articles, updates URL statuses. |
| `config/config_scrape.py` | Shared request headers/cookies used for HTTP fetches. |
| `scrap_function/utility.py` | Date parsing and source-specific extraction helpers (default, enrichment, EnergyTech GraphQL). |
| `boiler_markers.py` | Boilerplate strings to remove from paragraphs. |
| `keywords.py` | `SUBSIDY_KEYWORDS` used to tag subsidy-related articles. |
| `backfill_boiler_markers.py` | Cleanup utility for already-scraped articles (dry run by default). |
| `seedExistingUrls.ipynb` | Notebook for URL seeding/backfill workflows. |

## Required environment variables

Define these in your local `.env` (do not commit it):

- `MONGO_URI`
- `MONGO_DB_NAME`
- `MONGO_DB_URLS_COLLECTION`
- `MONGO_DB_ARTICLES_COLLECTION_NAME`

## Setup

From project root, create/activate your Python environment and install dependencies used by this module:

- `pymongo`
- `requests`
- `beautifulsoup4`
- `python-dateutil`
- `python-dotenv`
- `certifi`
- `trafilatura`

## Run

From the `scrape/` folder:

```bash
python scrape-articles.py
```

Optional flags:

```bash
# Scrape only one category
python scrape-articles.py --category enrichment

# Limit number of URLs processed
python scrape-articles.py --limit 50

# Combine both
python scrape-articles.py --category enrichment --limit 50
```

## Extraction behavior

- **Default path:** `requests` + BeautifulSoup paragraph extraction.
- **`enrichment` category:** readability-style extraction via `trafilatura`.
- **`energytech` category:** dedicated GraphQL extraction helper.
- **Keyword filter:** non-enrichment articles must match project-related keywords or are marked `irrelevant`.
- **Subsidy tag:** if subsidy terms are found, `meta.subsidy` is set to `true`.

## Backfill cleanup utility

Use this to re-clean paragraph text for already-scraped articles:

```bash
# Preview only (default)
python backfill_boiler_markers.py --dry-run

# Apply writes
python backfill_boiler_markers.py --no-dry-run

# Optional scope controls
python backfill_boiler_markers.py --category electrive --limit 1000
```

## Notes

- This module expects URLs to already exist in MongoDB (usually from `crawl/`).
- If you are preparing a public repo, keep `.env`, logs, and notebook checkpoints out of git.
