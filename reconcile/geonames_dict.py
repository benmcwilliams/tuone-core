import sys; sys.path.append("..")
import os
import time
import logging
from datetime import datetime, timezone
from mongo_client import mongo_client, test_articles_collection, articles_collection
from reconcile.src.step_2 import standardize_country, get_adm_level
import pandas as pd

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
    ).limit(2)
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

            if logger:
                logger.info(f"📍 Starting GeoNames lookup for city='{city}', country='{country}'")
            if not city:
                if logger:
                    logger.warning("⚠️ Skipping: city is empty or invalid")

            factory_data = {
                "type": node.get("type"),
                "ctry": country,
                "ctry_standard": std_country,
                "ctry_iso2": iso2,
                "ctry_failed": country_failed,
                "city": city
            }

            # Default ADM fields
            for level in range(1, 4):
                factory_data[f"adm_{level}"] = None
                factory_data[f"adm_{level}_code"] = None

            factory_data["lat"] = None
            factory_data["lon"] = None
            factory_data["adm_max_level"] = None

            if not country_failed and city:
                last_valid_lat = None
                last_valid_lon = None
                last_valid_level = None

                for level in range(1, 4):
                    if logger:
                        logger.info(f"🔍 Querying ADM{level} for city='{city}', country='{std_country}'")

                    name, code, lat, lon, failed = get_adm_level(city, iso2, level, logger=logger)

                    if not failed and name:
                        if logger:
                            logger.info(f"✅ ADM{level} success: {name}, code={code}, lat={lat}, lon={lon}")
                        factory_data[f"adm_{level}"] = name
                        factory_data[f"adm_{level}_code"] = code
                        last_valid_lat = lat
                        last_valid_lon = lon
                        last_valid_level = level
                    else:
                        if logger:
                            logger.warning(f"❌ ADM{level} lookup failed for city='{city}', iso2='{iso2}'")
                
                factory_data["lat"] = last_valid_lat
                factory_data["lon"] = last_valid_lon
                factory_data["adm_max_level"] = last_valid_level
            
            factory_nodes.append(factory_data)

# Step 3 (optional): Convert to DataFrame for inspection

df_factories = pd.DataFrame(factory_nodes)

# Display or return
print(df_factories.head(20))

df_factories.to_excel("test_geonames.xlsx")