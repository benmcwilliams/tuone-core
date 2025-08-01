import sys; sys.path.append("..")
import os
import time
import logging
from pymongo import UpdateOne
#from datetime import datetime, timezone
from mongo_client import articles_collection, geonames_collection
from src.step_2 import standardize_country, get_adm_level
from src.geonames_helpers import clean_city, clean_country, normalize_city_key
from src.logger import setup_city_logger
import re

system_logger = logging.getLogger("main")

def query_geonames_new_cities():

    # 1) load existing entries from mongoDB-geonames-collection (both cases which succeeded and failed)
    existing_entries = geonames_collection.find({})
    existing_pairs = set()

    for doc in existing_entries:
        country = doc["ctry_standard"]
        for city_key in doc.get("cities", {}).keys():
            existing_pairs.add((country, city_key))
        for city_key in doc.get("failures", []):
            existing_pairs.add((country, city_key))

    system_logger.info(f"📦 Loaded {len(existing_pairs)} existing (country, city_key) pairs from MongoDB.")

    # 2) mongodb filter to only return cases where article has at least one node with type == factory
    filtered_articles = list(
        articles_collection.find(
            {
                "meta.category": "pvmagazine",
                "nodes": {
                    "$elemMatch": {"type": "factory"}
                }
            },
            {"nodes": 1, "_id":1}
        )
    )

    system_logger.info(f"📰 Found {len(filtered_articles)} article(s) containing factory nodes.")

    # 3) extract unique candidate (country, city) pairs. These are present in our articles_collection but not already queried through geonames.

    candidates = set()
    metadata = {}

    for doc in filtered_articles:
        article_id = doc.get("_id")
        for node in doc.get("nodes", []):
            if node.get("type") == "factory":

                location = node.get("location") or {}
                city = clean_city(location.get("city"))
                country = clean_country(location.get("country"))

                std_country, iso2, country_failed = standardize_country(country)

                if not city or country_failed:
                    continue

                key = (std_country, normalize_city_key(city))
                if key not in existing_pairs:
                    candidates.add(key)

                    #metadata[key] = {"iso2":iso2, "original_country": country}
                    if key not in metadata:
                        metadata[key] = {
                            "iso2": iso2,
                            "original_country": country,
                            "original_city": city,
                            "article_ids": [article_id]
                        }
                    else:
                        metadata[key]["article_ids"].append(article_id)

    system_logger.info(f"🧹 Identified {len(candidates)} new (country, city) pairs to query. Example three:")
    system_logger.info(list(candidates)[:3])

    # 4) query the geoname API to return geographic data for any new locations & prepare bulk update

    updates = []

    for (std_country, city) in sorted(candidates):
        iso2 = metadata[(std_country,city)]["iso2"]
        original_country = metadata[(std_country, city)]["original_country"]

        logger = setup_city_logger(iso2, city)
        article_ids = metadata[(std_country, city)]["article_ids"]
        logger.info(f"🗺️ Starting GeoNames lookup for city='{city}', country='{original_country}'")
        logger.info(f"📍 Location is present in the following articles: {article_ids}")

        city_to_query = metadata[(std_country, city)]["original_city"]
        name, adm1, adm2, adm3, adm4, bbox, failed = get_adm_level(city_to_query, iso2, logger=logger)

        if failed or not name:
            logger.warning(f"❌ Lookup failed for city='{city}', iso2='{iso2}'")

            city_key = normalize_city_key(city)

            update = UpdateOne(
                {"ctry_standard": std_country},
                {"$addToSet": {"failures": city_key}},  # avoids duplicates
                upsert=True,
            )
            updates.append(update)
            continue

        logger.info(f"✅ Success. Writing to DB for: {std_country} – {city}")
        city_key = normalize_city_key(city)

        update = UpdateOne(
            {"ctry_standard": std_country},
            {
                    "$setOnInsert": {"ctry_standard": std_country, "ctry_iso2": iso2},
                    "$set": {
                        f"cities.{city_key}" : {
                        "name": name,
                        "adm1": adm1,
                        "adm2": adm2,
                        "adm3": adm3,
                        "adm4": adm4,
                        "bbox": bbox,
                        }
                    },
            },
            upsert=True,
        )

        updates.append(update)

    # 5) commit updates to mongodb

    if updates:
        result = geonames_collection.bulk_write(updates)
        system_logger.info(f"✅ Geonames MongoDB updated. Inserted: {result.upserted_count}, Modified: {result.modified_count}")
    else:
        system_logger.info("📭 No new updates to write.")