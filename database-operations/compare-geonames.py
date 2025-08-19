# Assumes `db` is already defined and points to your MongoDB database.
# Example: from mongo_client import db

# mongo_client_setup.py
import os

import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import logging

MONGO_URI = "mongodb+srv://greeneconomy:oPHHBBAsFBAPfXyZ@tuone.lgh1dw4.mongodb.net/?retryWrites=true&w=majority&appName=tuone"
DB_NAME = "tuone"

mongo_client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
db = mongo_client[DB_NAME]

from typing import List, Set, Tuple

def extract_names(coll_name: str, country: str) -> Tuple[list[str], list[str]]:

    """
    Return sorted (city_names, failure_names) for a single country (ctry_standard exact match).
    """

    coll = db[coll_name]
    projection = {"cities": 1, "failures": 1}
    query = {"ctry_standard": country}

    city_names_set: Set[str] = set()
    failure_names_set: Set[str] = set()

    for doc in coll.find(query, projection):
        # cities → collect human-readable names
        cities = doc.get("cities") or {}
        for info in cities.values():
            if isinstance(info, dict):
                name = info.get("name")
                if name:
                    city_names_set.add(str(name))

        # failures → collect city_key (legacy string or dict)
        for f in (doc.get("failures") or []):
            if isinstance(f, str):
                failure_names_set.add(f)
            elif isinstance(f, dict):
                ck = f.get("city_key")
                if ck:
                    failure_names_set.add(str(ck))

    # dedupe + alphabetical
    city_names = sorted(city_names_set, key=lambda s: s.lower())
    failure_names = sorted(failure_names_set, key=lambda s: s.lower())
    return city_names, failure_names

def write_lines(path: str, lines: List[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(f"{line}\n")

if __name__ == "__main__":
    country = "Germany"   # 👈 change this to whichever country you want
    for coll in ("geonames_lookup", "geonames_store"):
        cities, failures = extract_names(coll, country)
        write_lines(f"{coll}_{country}_cities.txt", cities)
        write_lines(f"{coll}_{country}_failures.txt", failures)
        print(f"[{coll}] {country}: wrote {len(cities)} cities and {len(failures)} failures")