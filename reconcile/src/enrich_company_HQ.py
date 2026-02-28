"""
HQ Enrichment: Mongo ⟷ Excel sync with optional enrichment
- Reads Mongo (facilities)
- Ensures Excel buffer exists (hq_enrichment_results.xlsx) with intuitive columns
- User edits HQ_ISO2 directly in Excel (preserved across runs)
- Optional enrichment for only-missing values (answer 'y' when prompted)
- Writes updates back to Mongo (preserving user edits)
"""
 
from __future__ import annotations
 
import os
import sys
import time
from datetime import datetime
from pathlib import Path
 
import pandas as pd
from tqdm import tqdm
import pycountry

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
 
# Your existing internal modules
# - db: a pymongo database handle (from your mongo_client.py)
# - get_headquarters_country(name, raw_name=None) and country_to_iso2(name)
from mongo_client import db
from reconcile.src.country_hq import get_headquarters_country, country_to_iso2
 
# --------------------------
# CONFIG
# --------------------------
COLLECTION_NAME = "facilities"
 
# Excel buffer (created next to this script)
OUTPUT_FILE = Path(__file__).with_name("hq_enrichment_results.xlsx")
 
# Set True to also store full country/region fields in Mongo (besides ISO2)
WRITE_EXTRA_FIELDS = True

# Filter: only process facilities with these product_lv1 values
ALLOWED_PRODUCT_LV1 = ["battery", "solar", "vehicle", "iron", "wind"]

# Gentle rate limiting for enrichment
SLEEP_BETWEEN_LOOKUPS_SEC = 0.12

def iso2_to_country_name(iso2: str | None) -> str | None:
    """Convert ISO2 code to full country name using pycountry."""
    if not iso2:
        return None
    try:
        country = pycountry.countries.get(alpha_2=iso2.upper())
        return country.name if country else None
    except (KeyError, AttributeError):
        return None

# Simple region mapper (edit as needed)
EUROPE_ISO2 = {
    "AL","AD","AM","AT","AZ","BA","BE","BG","BY","CH","CY","CZ","DE","DK","EE","ES","FI",
    "FR","GB","UK","GR","HR","HU","IE","IS","IT","LI","LT","LU","LV","MC","MD","ME","MK",
    "MT","NL","NO","PL","PT","RO","RS","RU","SE","SI","SK","SM","UA","VA"
}
def iso2_to_region(iso2: str | None) -> str | None:
    if not iso2:
        return None
    iso = iso2.upper()
    if iso in EUROPE_ISO2: return "Europe"
    if iso == "CN": return "China"
    if iso == "IN": return "India"
    if iso == "KR": return "South Korea"
    if iso == "JP": return "Japan"
    if iso == "US": return "United States"
    if iso == "JV": return "Joint Venture"
    return "Other"
 

# --------------------------
# DATA IO HELPERS
# --------------------------
def fetch_mongo_snapshot():
    """
    Pull a snapshot of (inst_canon + current HQ fields) from Mongo.
    We allow duplicates in Mongo but aggregate to one row per inst_canon here.
    """
    coll = db[COLLECTION_NAME]
    # Pull only fields we care about, filtered by product_lv1
    docs = list(
        coll.find(
            {"product_lv1": {"$in": ALLOWED_PRODUCT_LV1}},
            {
                "_id": 0,
                "inst_canon": 1,
                "inst_canon_ctry_hq": 1,       # ISO2 already stored (if any)
                "inst_canon_hq_country": 1,     # optional, may not exist yet
                "inst_canon_hq_region": 1,      # optional, may not exist yet
            },
        )
    )
    if not docs:
        return pd.DataFrame(columns=["inst_canon", "inst_canon_ctry_hq",
                                     "inst_canon_hq_country", "inst_canon_hq_region"])
 
    df = pd.DataFrame(docs)
 
    # Ensure expected columns exist
    for col in ["inst_canon", "inst_canon_ctry_hq", "inst_canon_hq_country", "inst_canon_hq_region"]:
        if col not in df.columns:
            df[col] = None
 
    # Deduplicate to one row per inst_canon, preferring first non-null
    df.sort_values(by=["inst_canon"], inplace=True, ignore_index=True)
 
    # Aggregate: take first non-null per column
    agg = (
        df.groupby("inst_canon", as_index=False)
          .agg({
              "inst_canon_ctry_hq": "first",
              "inst_canon_hq_country": "first",
              "inst_canon_hq_region": "first",
          })
    )
    return agg
 
 
def ensure_excel_columns(df_excel: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure the Excel buffer has the intuitive columns:
    - inst_canon
    - HQ_ISO2 (editable - user edits this 2-digit code, country/region auto-computed internally)
    """
    expected = ["inst_canon", "HQ_ISO2"]
    for col in expected:
        if col not in df_excel.columns:
            df_excel[col] = None
    # Keep only expected + anything else the team may have added (we’ll place expected first)
    ordered = [c for c in expected if c in df_excel.columns] + [c for c in df_excel.columns if c not in expected]
    return df_excel[ordered]
 
 
def load_or_create_excel_buffer(insts: pd.Series) -> pd.DataFrame:
    """
    If Excel exists, load it and ensure columns. If not, create a blank buffer
    with the right columns for all inst_canon values currently in Mongo.
    """
    if OUTPUT_FILE.exists():
        xdf = pd.read_excel(OUTPUT_FILE)
        xdf = ensure_excel_columns(xdf)
        # Merge current list of inst_canon from Mongo, adding any new ones not present in Excel yet
        merged = insts.to_frame().merge(xdf, on="inst_canon", how="left")
        merged = ensure_excel_columns(merged)
        return merged
    else:
        xdf = pd.DataFrame({"inst_canon": insts})
        xdf = ensure_excel_columns(xdf)
        return xdf
 
 
def write_excel_safely(df: pd.DataFrame, path: Path):
    """Write Excel; if locked by Excel, write an autosave copy."""
    try:
        df.to_excel(path, index=False)
        print(f"💾 Excel snapshot written: {path.name}")
    except PermissionError:
        alt = path.with_name(path.stem + "_autosave.xlsx")
        df.to_excel(alt, index=False)
        print(f"⚠️ {path.name} is open/locked. Wrote autosave instead: {alt.name}")
 

# --------------------------
# CORE PIPELINE
# --------------------------

def main():
    print(f"\n🔗 Connecting to Mongo collection: {COLLECTION_NAME}")
    df_mongo = fetch_mongo_snapshot()
 
    # Ensure we have at least the inst_canon column
    # if "inst_canon" not in df_mongo.columns:
    #     df_mongo["inst_canon"] = None
    df_mongo = df_mongo[df_mongo["inst_canon"].notna()].copy()
    df_mongo.sort_values("inst_canon", inplace=True, ignore_index=True)
 
    if df_mongo.empty:
        print("ℹ️ No documents found in Mongo with 'inst_canon'. Nothing to do.")
        return
 
    # Prepare the Excel buffer
    excel_df = load_or_create_excel_buffer(df_mongo["inst_canon"])
 
    # Hydrate Excel buffer with current Mongo state for visibility
    # (only fill Excel ISO2 where empty - preserves user edits)
    # Country and region will be auto-computed from ISO2 below
    excel_df["HQ_ISO2"] = excel_df["HQ_ISO2"].fillna(df_mongo.set_index("inst_canon")["inst_canon_ctry_hq"])
 
    # Decide whether to enrich now (missing-only)
    do_enrich = input("\n⚙️  Run enrichment for missing HQ ISO2 values? (y/n): ").strip().lower() == "y"
 
    # Build a working table (merged view)
    work = excel_df.copy()
    
    # Initialize internal columns (not shown in Excel but needed for enrichment/MongoDB)
    if "Name_manual" not in work.columns:
        work["Name_manual"] = None
    if "HQ_country" not in work.columns:
        work["HQ_country"] = None
    if "HQ_region" not in work.columns:
        work["HQ_region"] = None

    # Use HQ_ISO2 directly (user edits are preserved via fillna above)
    work["HQ_ISO2_final"] = work["HQ_ISO2"]
    # Now enrich only rows still missing HQ_ISO2_final
    need_enrichment_idx = work.index[work["HQ_ISO2_final"].isna()]

    enriched_count = 0
    manual_applied = work["HQ_ISO2"].notna().sum()
 
    if do_enrich and len(need_enrichment_idx) > 0:
        print(f"🌍 Enriching {len(need_enrichment_idx)} companies (missing ISO2 only)...")
        for i in tqdm(need_enrichment_idx, desc="Enrichment"):
            row = work.loc[i]
            name_for_lookup = row["Name_manual"] if pd.notna(row["Name_manual"]) and str(row["Name_manual"]).strip() else row["inst_canon"]
 
            country_full = get_headquarters_country(str(name_for_lookup))
            if country_full:
                iso2 = country_to_iso2(country_full)
                work.at[i, "HQ_ISO2_final"] = iso2
                work.at[i, "HQ_ISO2"] = iso2  # keep Excel auto column in sync
                # Auto-compute country name and region from ISO2
                work.at[i, "HQ_country"] = iso2_to_country_name(iso2)
                work.at[i, "HQ_region"] = iso2_to_region(iso2)
                enriched_count += 1
            else:
                # leave as NaN if no match
                pass
            time.sleep(SLEEP_BETWEEN_LOOKUPS_SEC)
    else:
        if do_enrich:
            print("✅ Nothing to enrich — all ISO2 values are present.")
        else:
            print("⏭️  Skipping enrichment (quick sync mode).")

    # Auto-compute country name and region for all rows with ISO2 (ensures consistency)
    # This ensures country/region are always derived from ISO2, not manually entered
    rows_with_iso2 = work.index[work["HQ_ISO2"].notna()]
    for i in rows_with_iso2:
        iso2 = str(work.at[i, "HQ_ISO2"]).upper().strip()
        work.at[i, "HQ_ISO2_final"] = iso2
        work.at[i, "HQ_country"] = iso2_to_country_name(iso2)
        work.at[i, "HQ_region"] = iso2_to_region(iso2)
 
    # --------------------------
    # WRITE BACK TO MONGO
    # --------------------------
    coll = db[COLLECTION_NAME]
    updated_docs = 0
    skipped_docs_existing = 0
 
    # Build lookups of current Mongo values to check if updates are needed
    mongo_iso_lookup = df_mongo.set_index("inst_canon")["inst_canon_ctry_hq"].to_dict()
    mongo_country_lookup = df_mongo.set_index("inst_canon")["inst_canon_hq_country"].to_dict() if WRITE_EXTRA_FIELDS else {}
    mongo_region_lookup = df_mongo.set_index("inst_canon")["inst_canon_hq_region"].to_dict() if WRITE_EXTRA_FIELDS else {}

    for _, r in work.iterrows():
        canon = r["inst_canon"]
        final_iso2 = r.get("HQ_ISO2_final")

        # If no ISO2 at all, skip
        if pd.isna(final_iso2) or not str(final_iso2).strip():
            continue

        final_iso2 = str(final_iso2).upper()
        current_iso2 = mongo_iso_lookup.get(canon)

        # Prepare update payload
        update = {
            "inst_canon_ctry_hq": final_iso2,
            "updated_at": datetime.utcnow(),
        }

        if WRITE_EXTRA_FIELDS:
            # These extra fields are optional; okay if they didn't exist before
            hq_country = r.get("HQ_country")
            hq_region = r.get("HQ_region")
            if pd.notna(hq_country) and str(hq_country).strip():
                update["inst_canon_hq_country"] = str(hq_country)
            if pd.notna(hq_region) and str(hq_region).strip():
                update["inst_canon_hq_region"] = str(hq_region)

        # Check if any field has changed
        iso2_changed = not current_iso2 or str(current_iso2).upper() != final_iso2
        
        country_changed = False
        region_changed = False
        if WRITE_EXTRA_FIELDS:
            current_country = mongo_country_lookup.get(canon)
            current_region = mongo_region_lookup.get(canon)
            excel_country = update.get("inst_canon_hq_country")
            excel_region = update.get("inst_canon_hq_region")
            
            # Country changed if Excel has value and (Mongo doesn't or values differ)
            if excel_country:
                country_changed = (not current_country or str(current_country).strip() != str(excel_country).strip())
            # Region changed if Excel has value and (Mongo doesn't or values differ)
            if excel_region:
                region_changed = (not current_region or str(current_region).strip() != str(excel_region).strip())

        # Skip only if nothing changed
        if not iso2_changed and not country_changed and not region_changed:
            skipped_docs_existing += 1
            continue

        res = coll.update_many({"inst_canon": canon}, {"$set": update})
        updated_docs += res.modified_count
 
    # --------------------------
    # SAVE/REFRESH EXCEL BUFFER
    # --------------------------
    # Keep only the editable columns in Excel (country/region are auto-computed internally)
    excel_out = work[["inst_canon", "HQ_ISO2"]].copy()
    excel_out.sort_values("inst_canon", inplace=True, ignore_index=True)
    write_excel_safely(excel_out, OUTPUT_FILE)
 
    # --------------------------
    # SUMMARY
    # --------------------------
    total_inst = len(work)
    available_iso2 = work["HQ_ISO2_final"].notna().sum()
    print("\n📊 Summary")
    print(f"  Companies total:                {total_inst}")
    print(f"  With ISO2 set:                  {manual_applied}")
    print(f"  Enriched (missing-only):        {enriched_count}")
    print(f"  With ISO2 available (final):    {available_iso2}")
    print(f"  Mongo docs updated:             {updated_docs}")
    print(f"  Skipped (already up-to-date):   {skipped_docs_existing}")
    print("\n✅ Done.\n")
 
 
if __name__ == "__main__":
    # Make sure pandas prints won't choke on very wide columns if you debug locally
    pd.set_option("display.width", 180)
    pd.set_option("display.max_columns", 50)
    main()