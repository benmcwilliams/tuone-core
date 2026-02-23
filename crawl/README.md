# Crawl

News-URL crawlers for energy, cleantech, and industry sources. Each crawler discovers article URLs from a given source, deduplicates against existing data, and stores **new** URLs in MongoDB for later scraping or processing.

## What it does

- **Input:** Configured sources (sites, channels, sitemaps).
- **Output:** New URLs written to a shared MongoDB collection, with `category` (source name) and optional `status: 'new'`.
- **Deduplication:** Existing URLs per category are read from the DB; only URLs not already stored are inserted.

## Structure

| Path | Role |
|------|------|
| `crawler.py` | Entry point: runs all crawlers in sequence (with optional per-source page limits). |
| `config/config_crawl.py` | Source config: channel IDs, URL extensions, page types (World Energy, PV Magazine, ReNews.biz, Electrive, etc.). |
| `mongodb_util.py` | MongoDB helpers: `get_mongo_collection()`, `get_existing_urls()`, `save_new_urls()`. |
| `crawlers/` | One module per source; each exposes a crawler function (e.g. `electrive_crawler`, `pv_magazine_crawler`). |
| `logs/` | `main_crawler.log` — crawl run log (overwritten each run). |

## Crawlers (sources)

| Module | Source | Method |
|--------|--------|--------|
| `crawley_world_energy` | World Energy | Channels (hydropower, nuclear, solar, wind, hydrogen, geothermal, battery, vehicles) |
| `crawley_pv_magazine` | PV Magazine | Category pages (hydrogen, manufacturing, utility, balance-of-system, energy-storage) |
| `crawley_pv_tech` | PV Tech | Paginated listing |
| `crawley_renewsBiz` | ReNews.biz | Offshore/onshore wind, solar |
| `crawley_offshorewindbiz` | Offshore Wind Biz | Listing pages |
| `crawley_electrive` | Electrive | Automobile, battery/fuel-cell categories (Selenium) |
| `crawley_power_technology` | Power Technology | Paginated listing |
| `crawley_just_auto` | Just Auto | Sitemap(s) |
| `crawley_battery_news` | Battery News | Sitemap/listing |
| `crawley_glass_international` | Glass International | Listing/category |
| `crawley_transformers` | Transformers Magazine | Listing/category |
| `crawley_energy_tech` | Aspire EnergyTech | GraphQL (optional; currently commented out in `crawler.py`) |

Crawlers use either **HTTP + BeautifulSoup** or **Selenium** (e.g. Electrive) depending on the site.

## Setup and run

1. **Environment:** From project root (or `crawl/`), ensure a `.env` with:
   - `MONGO_URI` — MongoDB connection string  
   - `MONGO_DB_NAME` — Database name  
   - `MONGO_URLS_NAME` — Collection name for URLs  

2. **Dependencies:** Python env with `pymongo`, `requests`, `beautifulsoup4`, `selenium`, `webdriver-manager`, `python-dotenv`, `certifi` (and Chrome for Selenium crawlers).

3. **Run all crawlers:**
   ```bash
   cd crawl && python crawler.py
   ```
   Logs go to `logs/main_crawler.log` and to the console.

4. **Tuning:** In `crawler.py`, per-source `max_pages` (and which crawlers are commented in/out) control how much is crawled each run.

## Notes

- Each crawler is independent: it gets the shared collection, loads existing URLs for its `category`, then inserts only new URLs.
- Electrive uses headless Chrome (ChromeDriverManager); others use `requests` + BeautifulSoup or sitemap parsing.
- Aspire EnergyTech (GraphQL) is present but disabled in the main script; enable and set `skip`/`limit` in `crawler.py` if needed.
