import sys; sys.path.append("..")
import os
import time
import logging
from datetime import datetime, timezone
from mongo_client import mongo_client, test_articles_collection, articles_collection
from reconcile.src.step_2 import standardize_country, get_adm_level
import pandas as pd

# load existing results (if file exists)
existing_path = "storage/output/geonames.xlsx"
if os.path.exists(existing_path):
    existing_df = pd.read_excel(existing_path)
    existing_pairs = set(zip(existing_df["ctry_standard"], existing_df["city"]))
else:
    existing_df = pd.DataFrame()
    existing_pairs = set()

def clean_city(city_raw):
    if city_raw is None:
        return ""
    city = str(city_raw).strip().lower()
    if city in {"", "null", "none", "nan", "unknown", "tbd"}:
        return ""
    return city

# initiate logging
def setup_city_logger(country, city, logs_dir="logs/logs_geonames"):
    os.makedirs(logs_dir, exist_ok=True)
    name = f"{country}_{city}".replace(" ", "_").lower()
    log_path = os.path.join(logs_dir, f"{name}.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # don’t duplicate to root

    if not logger.handlers:
        fh = logging.FileHandler(log_path, mode="w")
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger

# set up mongodb filter to only return cases where article has at least one node with type == factory
filtered_articles = list(
    articles_collection.find(
        {
            "meta.category": "electrive",
            "nodes": {
                "$elemMatch": {
                    "type": "factory"
                }
            }
        },
        {"nodes": 1}
    ).limit(200)
)

print(f"Found {len(filtered_articles)} article(s) with nodes")

# Step 2: Extract and flatten all factory nodes with their city and country
factory_nodes = []

for doc in filtered_articles:
    for node in doc.get("nodes", []):
        if node.get("type") == "factory":
            location = node.get("location", {})

            city_raw = location.get("city")
            country_raw = location.get("country")

            # normalize inputs
            country = str(country_raw).strip().lower() if country_raw is not None else ""
            city = clean_city(city_raw)

            std_country, iso2, country_failed = standardize_country(country)

            # per city-country logger
            logger = setup_city_logger(std_country, city) if city and not country_failed else None

            if (std_country, city) in existing_pairs:
                if logger:
                    logger.info(f"⏭️ Skipping: already processed ({city}, {std_country})")
                continue

            if logger:
                logger.info(f"📍 Starting GeoNames lookup for city='{city}', country='{country}'")
            if not city:
                if logger:
                    logger.warning("⚠️ Skipping: city is empty or invalid")
                break

            factory_data = {
                "type": node.get("type"),
                "ctry": country,
                "ctry_standard": std_country,
                "ctry_iso2": iso2,
                "ctry_failed": country_failed,
                "city": city
            }

            if not country_failed and city:

                print(f"🔍 Querying for city='{city}', country='{std_country}'")
                name, adm1, adm2, adm3, adm4, bbox, failed = get_adm_level(city, iso2, logger=logger)

                if not failed and name:
                    factory_data["name"] = name
                    factory_data["adm1"] = adm1
                    factory_data["adm1"] = adm1
                    factory_data["adm2"] = adm2
                    factory_data["adm3"] = adm3
                    factory_data["adm4"] = adm4
                    factory_data["bbox"] = bbox

                else:
                    logger.warning(f"❌ lookup failed for city='{city}', iso2='{iso2}'")
            
            factory_nodes.append(factory_data)

# Step 3 (optional): Convert to DataFrame for inspection
df_factories = pd.DataFrame(factory_nodes)

# Combine with existing if needed
if not existing_df.empty:
    combined_df = pd.concat([existing_df, df_factories], ignore_index=True)
else:
    combined_df = df_factories

combined_df.to_excel(existing_path, index=False)

# Display or return
print(combined_df.head(5))

combined_df.sort_values(by=["ctry_standard", "city"], inplace=True)

combined_df.drop_duplicates(subset=["ctry_standard", "city", "name", "adm1"], inplace=True)
combined_df.to_excel("storage/output/geonames.xlsx", index=False)