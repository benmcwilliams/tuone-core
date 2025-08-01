import sys; sys.path.append("../..")
from mongo_client import geonames_collection

# script defines logic for reading in geonames mapping from the Mongo collection, which we apply in b_merge.py.

def build_geo_lookup():
    geo_lookup = {}
    for doc in geonames_collection.find():
        iso2 = doc.get("ctry_iso2", "").upper()
        cities = doc.get("cities", {})
        if not iso2:
            continue
        geo_lookup.setdefault(iso2, {}).update(cities)
    return geo_lookup

def get_geo_value(row, key, geo_lookup):
    iso2 = row["iso2"]
    city_key = row["city_key"]
    return geo_lookup.get(iso2, {}).get(city_key, {}).get(key)