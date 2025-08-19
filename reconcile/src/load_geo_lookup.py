import sys; sys.path.append("../..")
import json
import os
from mongo_client import geonames_collection
from src.config import GEO_LOOKUP_JSON
import logging

# script defines logic for reading in geonames mapping from the Mongo collection, which we apply in b_merge.py.

def build_geo_lookup(save_to_disk: bool = True):
    geo_lookup = {}
    for doc in geonames_collection.find():
        iso2 = doc.get("ctry_iso2", "").upper()
        cities = doc.get("cities", {})
        if not iso2:
            continue
        geo_lookup.setdefault(iso2, {}).update(cities)
    if save_to_disk:
        try:
            os.makedirs(os.path.dirname(GEO_LOOKUP_JSON), exist_ok=True)
            with open(GEO_LOOKUP_JSON, "w", encoding="utf-8") as f:
                json.dump(geo_lookup, f, ensure_ascii=False)
            logging.info(f"💾 Saved geo_lookup to {GEO_LOOKUP_JSON}")
        except Exception as e:
            logging.warning(f"Failed to save geo_lookup to {GEO_LOOKUP_JSON}: {e}")
    return geo_lookup

def get_geo_value(row, key, geo_lookup):
    iso2 = row["iso2"]
    city_key = row["city_key"]
    return geo_lookup.get(iso2, {}).get(city_key, {}).get(key)