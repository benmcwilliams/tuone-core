import sys; sys.path.append("..")
import os
import time
import logging
from datetime import datetime, timezone
from mongo_client import mongo_client, test_articles_collection
from reconcile.src.step_2 import standardize_country, get_adm_level
from dotenv import load_dotenv

load_dotenv()

# Create log directory
log_dir = "logs/logs_geonames"
os.makedirs(log_dir, exist_ok=True)

# Configure logging

def get_article_logger(article_id) -> logging.Logger:
    logger = logging.getLogger(str(article_id))
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        log_path = os.path.join(log_dir, f"{article_id}.log")
        handler = logging.FileHandler(log_path, mode='w')
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

# 1. Query MongoDB for entries needing enrichment

query = {
    "factory_geonames_enriched_at": {"$exists": False},  # skip already-processed
    "nodes": {
        "$elemMatch": {
            "type": "factory",
            "location.city": {"$exists": True, "$nin": [None, "", "null", "nan"]},
            "location.country": {"$exists": True, "$nin": [None, "", "null", "nan"]},
            "$or": [
                {"location.factory_city_adm1_name": {"$exists": False}},
                {"location.factory_city_adm1_name": None}
            ]
        }
    }
}

entries = list(test_articles_collection.find(query))
print(f"Found {len(entries)} article(s) with unenriched factory location(s)")

# ------------------- Processing loop -------------------
for doc in entries:
    article_id = doc["_id"]
    title = doc.get("title", "No Title")
    logger = get_article_logger(article_id)
    logger.info(f"Processing article: {title}")

    updated = False

    for node in doc.get("nodes", []):
        if node.get("type") != "factory":
            continue

        loc = node.get("location", {})
        city_raw = loc.get("city")
        country_raw = loc.get("country")

        # Normalize inputs
        city = str(city_raw).strip().lower() if city_raw is not None else ""
        country = str(country_raw).strip().lower() if country_raw is not None else ""

        # Skip if city or country are invalid
        if city in {"", "null", "nan"} or country in {"", "null", "nan"}:
            logger.warning(f"⚠️ Skipping factory with bad city/country: city='{city_raw}', country='{country_raw}'")
            continue

        if "factory_city_adm_name" in loc and loc["factory_city_adm_name"]:
            logger.info(f"Already enriched: {city}, {country}")
            continue

        logger.info(f"🔍 Factory: {city}, {country}")

        # --- Country standardization ---
        std_country, iso2, country_failed = standardize_country(country)
        loc["country_standardized"] = std_country
        loc["country_iso2"] = iso2
        loc["country_not_found"] = country_failed

        if country_failed:
            logger.warning(f"❌ Could not resolve country: {country}")
        else:
            logger.info(f"✅ Country standardized: {country} → {std_country} ({iso2})")

        # --- City lookup via GeoNames ---
        if not country_failed:

            last_valid_lat = None
            last_valid_lon = None
            last_valid_level = None

            for level in range(1, 4):
                name, code, lat, lon, failed = get_adm_level(city, iso2, level)
                if not failed and name:
                    logger.info(f"✅ GeoNames ADM{level} success: {name}, Code={code}, Lat={lat}, Lon={lon}")
                    loc[f"factory_city_adm{level}_name"] = name
                    loc[f"factory_city_adm{level}_code"] = code

                    # Store the latest lat/lon (from deepest successful match)
                    last_valid_lat = lat
                    last_valid_lon = lon
                    last_valid_level = level
                else:
                    logger.info(f"ADM{level} lookup failed")
                    break  # stop after first failure

            if last_valid_lat and last_valid_lon:
                loc["factory_city_latitude"] = last_valid_lat
                loc["factory_city_longitude"] = last_valid_lon
                loc["factory_city_adm_level"] = last_valid_level
                loc["factory_city_not_found"] = False
                updated = True
            else:
                logger.warning(f"❌ All ADM lookups failed for city: {city}")
                loc["factory_city_not_found"] = True
                updated = True
        else:
            loc["factory_city_not_found"] = True
            updated = True

        node["location"] = loc
        time.sleep(4)

    if updated:
        test_articles_collection.update_one(
            {"_id": article_id},
            {"$set": {"nodes": doc["nodes"],
                      "factory_geonames_enriched_at": datetime.now(timezone.utc)}}
        )
        logging.info(f"✓ Updated article {article_id} with enriched factory location(s)")

logging.info("🎉 Finished enrichment of factory nodes")