import sys; sys.path.append("..")
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple

from pymongo import UpdateOne
from mongo_client import articles_collection, geonames_collection
from src.step_2 import standardize_country, get_adm_level
from src.geonames_helpers import clean_city, clean_country, normalize_city_key
from src.logger import setup_city_logger
from src.inputs import EUROPEAN_COUNTRIES

system_logger = logging.getLogger("main")

Country = str
CityKey = str
Key = Tuple[Country, CityKey]

# For ("AT", "rainbach"), override the GeoNames query to "Rainbach im Mühlkreis", but store under "rainbach"
# LHS has the normalised city_key (direct from failures category), RHS is what to search geonames API for
# check whether - should be replaced with spaces (think correct)
CITY_QUERY_OVERRIDES: Dict[Tuple[str, CityKey], str] = {
    ("AT", "rainbach"): "Rainbach im Mühlkreis",
    ("AT", "vallach"): "Villach",
    ("BE", "foret"): "Forest",
    ("FR", "flins"): "Flins-sur-Seine",
    ("FR", "douvrai"): "Douvrin",
    ("FR", "burgundyfranchecomté"): "Bourgogne-Franche-Comté",
    ("FR", "dunkerque"): "Dunkirk",
    ("FR", "grand_poitiers"): "Grand-Pont",
    ("BG", "lowetsch"): "Lovech",
    ("BG", "silistra_municipality"): "Silistra",
    ("HU", "györ"): "Győr",
    ("HU", "györ"): "Győr",
    ("HU", "kekscemet"): "Kecskemét",
    ("HU", "goed"): "Göd",
    ("HU", "kömlöd"): "Kömlőd",
    ("HU", "lukacshaza"): "Lukácsháza"
}

# ---------- Data access ----------

def load_existing_pairs(include_failures: bool = True, failure_backoff_days: Optional[int] = 7) -> Set[Key]:
    """
    Return set of (ctry_standard, city_key) pairs that are already present in geonames_collection,
    including failures (optionally with backoff, so we don't hammer the same bad city).
    """
    existing: Set[Key] = set()
    projection = {"ctry_standard": 1, "cities": 1}
    if include_failures:
        projection["failures"] = 1

    for doc in geonames_collection.find({}, projection):
        ctry = doc.get("ctry_standard")
        if not ctry:
            continue

        # already-successful cities
        for city_key in (doc.get("cities") or {}).keys():
            existing.add((ctry, city_key))

        if include_failures:
            failures = doc.get("failures") or []
            cutoff = None
            if failure_backoff_days is not None:
                cutoff = datetime.utcnow() - timedelta(days=failure_backoff_days)

            # failures can be a list of strings (legacy) or list of dicts with last_attempt
            for f in failures:
                if isinstance(f, str):
                    existing.add((ctry, f))
                elif isinstance(f, dict):
                    ck = f.get("city_key")
                    last = f.get("last_attempt")
                    if ck and (cutoff is None or (isinstance(last, datetime) and last > cutoff)):
                        existing.add((ctry, ck))

    system_logger.info(f"📦 Loaded {len(existing)} existing (country, city_key) pairs from MongoDB.")
    return existing

def iter_factory_articles(limit: Optional[int] = 100, skip: int = 0) -> Iterator[dict]:
    query = {
        "nodes": {"$elemMatch": {"type": "factory"}},
    }
    projection = {"nodes": 1}  
    cursor = articles_collection.find(query, projection).skip(skip)
    if limit:
        cursor = cursor.limit(limit)
    yield from cursor


# ---------- Candidate extraction ----------
def collect_candidates(existing_pairs: Set[Key], limit: Optional[int] = None, skip: int = 0) -> Tuple[Set[Key], Dict[Key, dict]]:
    """
    Scan articles and produce candidate (std_country, city_key) pairs not yet in geonames_collection.
    Also return metadata for each candidate.
    """
    candidates: Set[Key] = set()
    metadata: Dict[Key, dict] = {}

    count_articles = 0
    for doc in iter_factory_articles(limit=limit, skip=skip):
        count_articles += 1
        article_id = doc.get("_id")
        for node in doc.get("nodes", []):
            if node.get("type") != "factory":
                continue

            location = node.get("location") or {}
            raw_city = clean_city(location.get("city"))
            raw_country = clean_country(location.get("country"))

            std_country, iso2, country_failed = standardize_country(raw_country)
            if not raw_city or country_failed:
                continue

            city_key = normalize_city_key(raw_city)
            key: Key = (std_country, city_key)

            if key in existing_pairs:
                continue

            entry = metadata.setdefault(
                key,
                {
                    "iso2": iso2,
                    "original_country": raw_country,
                    "original_city": raw_city,
                    "article_ids": set(),
                },
            )
            entry["article_ids"].add(article_id)
            candidates.add(key)

    system_logger.info(f"📰 Scanned {count_articles} article(s) with factory nodes.")
    system_logger.info(f"🧹 Identified {len(candidates)} new (country, city) pairs to query. Example three: {list(candidates)[:3]}")
    return candidates, metadata


# ---------- Update builders ----------

def build_failure_update(std_country: str, city_key: str) -> UpdateOne:
    # Store richer failure info so we can backoff retries
    fail_rec = {"city_key": city_key, "last_attempt": datetime.utcnow()}
    return UpdateOne(
        {"ctry_standard": std_country},
        {"$setOnInsert": {"ctry_standard": std_country},
         "$addToSet": {"failures": fail_rec}},
        upsert=True,
    )

def build_success_update(std_country: str, iso2: str, city_key: str, payload: dict) -> UpdateOne:
    return UpdateOne(
        {"ctry_standard": std_country},
        {
            "$setOnInsert": {"ctry_standard": std_country, "ctry_iso2": iso2},
            "$set": {f"cities.{city_key}": payload},
            # Optional: clean out a past failure record for this key if it exists
            "$pull": {"failures": {"city_key": city_key}},
        },
        upsert=True,
    )

# ---------- Core job ----------

def process_candidates(candidates: Set[Key], metadata: Dict[Key, dict], european_only: bool = True) -> List[UpdateOne]:
    updates: List[UpdateOne] = []

    for std_country, city_key in sorted(candidates):
        meta = metadata[(std_country, city_key)]
        iso2 = meta["iso2"]
        logger = setup_city_logger(iso2, city_key)

        if european_only and iso2 not in EUROPEAN_COUNTRIES:
            logger.info(f"⏭️ Skipping {iso2} - {std_country} (non-Europe).")
            continue

        original_country = meta["original_country"]
        original_city = meta["original_city"]
        article_ids = sorted(meta["article_ids"])

        # ---- override hook (only affects the query string) ----
        override_q = CITY_QUERY_OVERRIDES.get((iso2, city_key))
        query_city = override_q if override_q else original_city
        if override_q:
            logger.info(f"🔁 Override: '{original_city}' → '{query_city}' for {iso2}")

        logger.info(f"🗺️ Starting GeoNames lookup for city='{query_city}', country='{original_country}'")
        logger.info(f"📍 Location is present in the following articles: {article_ids}")

        name, adm1, adm2, adm3, adm4, bbox, failed, lat, lon = get_adm_level(query_city, iso2, logger=logger)

        if failed or not name:
            logger.warning(f"❌ Lookup failed for city='{city_key}', iso2='{iso2}'")
            updates.append(build_failure_update(std_country, city_key))
            continue

        logger.info(f"✅ Success. Writing to DB for: {std_country} – {city_key}")
        payload = {
            "name": name,
            "adm1": adm1,
            "adm2": adm2,
            "adm3": adm3,
            "adm4": adm4,
            "lat": float(lat) if lat is not None else None,
            "lon": float(lon) if lon is not None else None,
            "bbox": bbox
        }
        updates.append(build_success_update(std_country, iso2, city_key, payload))

    return updates


def commit_updates(updates: List[UpdateOne], batch_size: int = 1000) -> None:
    if not updates:
        system_logger.info("📭 No new updates to write.")
        return

    total_upserts = 0
    total_modified = 0

    for i in range(0, len(updates), batch_size):
        chunk = updates[i : i + batch_size]
        result = geonames_collection.bulk_write(chunk, ordered=False)
        total_upserts += getattr(result, "upserted_count", 0) or 0
        total_modified += getattr(result, "modified_count", 0) or 0

    system_logger.info(f"✅ Geonames MongoDB updated. Inserted: {total_upserts} fresh documents, Modified: {total_modified} documents.")


# ---------- Entry point ----------

def query_geonames_new_cities(limit: Optional[int] = 100, skip: int = 0) -> None:
    existing_pairs = load_existing_pairs(include_failures=True, failure_backoff_days=7)
    candidates, metadata = collect_candidates(existing_pairs, limit=limit, skip=skip)
    updates = process_candidates(candidates, metadata, european_only=True)
    commit_updates(updates)


if __name__ == "__main__":
    query_geonames_new_cities()