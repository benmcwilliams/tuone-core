import pandas as pd
import requests
import time
import random
from functools import lru_cache
from cleanco import basename
import pycountry
import difflib
import os
import certifi
 
# ============================================================
# CONFIGURATION
# ============================================================
FILE_PATH = r"C:\Users\benjamin.b-wade\Desktop\tuone_v6\reconcile\storage\input\CompanyNames.xlsx"
COLUMN_NAME = "inst_canon"
SAMPLE_SIZE = 100  # None for all
OUTPUT_PATH = r"C:\Users\benjamin.b-wade\Desktop\tuone_v6\reconcile\storage\output\cleaned_enriched_sample.xlsx"
 
WIKI_API = "https://en.wikipedia.org/w/api.php"
WD_API = "https://www.wikidata.org/w/api.php"
SPARQL_URL = "https://query.wikidata.org/sparql"
 
HEADERS = {"User-Agent": "Bruegel-CleanTech-Tracker/0.3 (benjamin.b-wade@bruegel.org)"}
 
# ============================================================
# NETWORK SAFETY LAYER
# ============================================================
def safe_get(url, params=None, headers=None, timeout=20, max_retries=4):
    """Retry GET requests with exponential backoff and SSL verification."""
    for attempt in range(max_retries):
        try:
            r = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
                verify=certifi.where(),
            )
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 5))
                print(f"⚠️ Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            wait = 2 ** attempt + random.random()
            print(f"⚠️ Request failed ({type(e).__name__}), retrying in {wait:.1f}s...")
            time.sleep(wait)
    print(f"❌ Request to {url} failed after {max_retries} retries.")
    return None
 
# ============================================================
# COUNTRY NORMALIZATION
# ============================================================
def country_to_iso2(name: str) -> str | None:
    if not name or not isinstance(name, str):
        return None
    name = name.strip().lower()
    replacements = {
        "people's republic of china": "china",
        "republic of china": "taiwan",
        "russian federation": "russia",
        "united states of america": "united states",
        "uk": "united kingdom",
        "england": "united kingdom",
        "scotland": "united kingdom",
        "wales": "united kingdom",
        "republic of korea": "south korea",
        "korea, republic of": "south korea",
        "democratic people's republic of korea": "north korea",
        "federal republic of germany": "germany",
        "kingdom of the netherlands": "netherlands",
    }
    if name in replacements:
        name = replacements[name]
 
    try:
        country = pycountry.countries.lookup(name)
        return country.alpha_2
    except LookupError:
        for c in pycountry.countries:
            if name in c.name.lower():
                return c.alpha_2
    return None
 
# ============================================================
# WIKIDATA HELPERS
# ============================================================
@lru_cache(maxsize=4096)
def title_to_qid(title: str):
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageprops",
        "redirects": 1,
        "titles": title,
    }
    r = safe_get(WIKI_API, params=params, headers=HEADERS, timeout=10)
    if not r:
        return None, None
    pages = r.json().get("query", {}).get("pages", {})
    for _, page in pages.items():
        qid = page.get("pageprops", {}).get("wikibase_item")
        if qid:
            return page.get("title"), qid
    return None, None
 
def wikipedia_search_title(name: str, limit=5):
    params = {
        "action": "query",
        "list": "search",
        "format": "json",
        "srsearch": name,
        "srlimit": limit,
    }
    r = safe_get(WIKI_API, params=params, headers=HEADERS, timeout=10)
    if not r:
        return []
    results = r.json().get("query", {}).get("search", [])
    return [r["title"] for r in results]
 
@lru_cache(maxsize=4096)
def wb_search_entities(name: str):
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "type": "item",
        "search": name,
        "limit": 7,
    }
    r = safe_get(WD_API, params=params, headers=HEADERS, timeout=10)
    if not r:
        return []
    return r.json().get("search", [])
 
def _score_candidate(cand, cleaned_name_lower):
    label = (cand.get("label") or "").lower()
    desc = (cand.get("description") or "").lower()
    score = difflib.SequenceMatcher(None, cleaned_name_lower, label).ratio() * 2
    if any(kw in desc for kw in ["company","enterprise","manufacturer","energy","group","industry","technology","bank","fund"]):
        score += 1.5
    if len(cleaned_name_lower.split()) < 2 and len(cleaned_name_lower) < 6:
        score -= 1
    return score
 
def is_company_entity(qid: str) -> bool:
    query = f"ASK {{ wd:{qid} wdt:P31/wdt:P279* wd:Q783794 . }}"
    r = safe_get(SPARQL_URL, params={"query": query, "format": "json"}, headers=HEADERS)
    if not r:
        return False
    return r.json().get("boolean", False)
 
@lru_cache(maxsize=4096)
def qid_to_country(qid: str):
    query = f"""
    SELECT ?countryLabel WHERE {{
      OPTIONAL {{ wd:{qid} wdt:P159 ?hq . ?hq wdt:P17 ?countryA . }}
      OPTIONAL {{ wd:{qid} wdt:P17  ?countryB . }}
      BIND(COALESCE(?countryA, ?countryB) AS ?country)
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }} LIMIT 1
    """
    r = safe_get(SPARQL_URL, params={"query": query, "format": "json"}, headers=HEADERS)
    if not r:
        return None
    results = r.json().get("results", {}).get("bindings", [])
    if results and "countryLabel" in results[0]:
        return results[0]["countryLabel"]["value"]
    return None
 
@lru_cache(maxsize=4096)
def search_qid_for_name(name: str):
    cleaned = name.strip()
    cleaned_lower = cleaned.lower()
 
    # 1. Try very explicit variants
    for variant in [
        cleaned,
        f"{cleaned}, Inc.",
        f"{cleaned} Inc",
        f"{cleaned} (company)",
        f"{cleaned} Corporation",
        f"{cleaned} Ltd",
        f"{cleaned} Group",
    ]:
        t, q = title_to_qid(variant)
        if q:
            return q
 
    # 2. Candidate search
    candidates = wb_search_entities(cleaned)
    if len(cleaned.split()) == 1 or len(cleaned) < 10:
        extra = wb_search_entities(f"{cleaned} company")
        if extra:
            seen = {c["id"] for c in candidates}
            candidates.extend([x for x in extra if x["id"] not in seen])
 
    if candidates:
        best, best_score = None, -1
        for cand in candidates:
            score = _score_candidate(cand, cleaned_lower)
            if score > best_score:
                best, best_score = cand, score
        if best and is_company_entity(best["id"]):
            return best["id"]
 
    # 3. Suffix fallback
    for suffix in ["AG","SA","Ltd","PLC","GmbH","Inc","Corp","NV","SpA"]:
        t, q = title_to_qid(f"{cleaned} {suffix}")
        if q:
            return q
 
    return None
 
 
 
 
def get_headquarters_country(cleaned_name: str, raw_name: str = None):
    """Pipeline: company name → QID → HQ country."""
 
    # --- Hardcoded fixes for known problematic companies ---
    name_lower = cleaned_name.lower()
    if name_lower in ["tesla", "tesla inc", "tesla motors"]:
        return "United States"
    if name_lower in ["byd", "byd auto", "byd company", "build your dreams"]:
        return "China"
 
    # --- Normal resolution pipeline ---
    qid = search_qid_for_name(cleaned_name)
    if not qid and raw_name:
        qid = search_qid_for_name(str(raw_name))
    if not qid:
        return None
    time.sleep(0.08)
    return qid_to_country(qid)