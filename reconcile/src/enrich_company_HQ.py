"""
HQ Enrichment: Mongo ⟷ Excel (manual overrides) with optional enrichment
- Reads Mongo (facilities_develop_2509)
- Ensures Excel buffer exists (hq_enrichment_results.xlsx) with intuitive columns
- Applies manual ISO2 overrides from Excel (HQ_ISO2_manual always wins)
- Optional enrichment for only-missing values (answer 'y' when prompted)
- Writes updates back to Mongo (preserving manual/existing data)
"""
 
from __future__ import annotations
 
import os
import sys
import time
from datetime import datetime
from pathlib import Path
 
import pandas as pd
from tqdm import tqdm
 
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
COLLECTION_NAME = "facilities_develop"
 
# Excel buffer (created next to this script)
OUTPUT_FILE = Path(__file__).with_name("hq_enrichment_results.xlsx")
 
# Set True to also store full country/region fields in Mongo (besides ISO2)
WRITE_EXTRA_FIELDS = True
 
# Gentle rate limiting for enrichment
SLEEP_BETWEEN_LOOKUPS_SEC = 0.12
 
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
    # Pull only fields we care about
    docs = list(
        coll.find(
            {},
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
    - Name_manual (optional manual name override for enrichment)
    - HQ_ISO2 (auto)
    - HQ_ISO2_manual (manual override; ALWAYS wins)
    - HQ_country (auto)
    - HQ_region (auto)
    """
    expected = ["inst_canon", "Name_manual", "HQ_ISO2", "HQ_ISO2_manual", "HQ_country", "HQ_region"]
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
    # (only fill Excel auto columns where they are empty)
    excel_df["HQ_ISO2"] = excel_df["HQ_ISO2"].fillna(df_mongo.set_index("inst_canon")["inst_canon_ctry_hq"])
    excel_df["HQ_country"] = excel_df["HQ_country"].fillna(df_mongo.set_index("inst_canon")["inst_canon_hq_country"])
    excel_df["HQ_region"] = excel_df["HQ_region"].fillna(df_mongo.set_index("inst_canon")["inst_canon_hq_region"])
 
    # Decide whether to enrich now (missing-only)
    do_enrich = input("\n⚙️  Run enrichment for missing HQ ISO2 values? (y/n): ").strip().lower() == "y"
 
    # Build a working table (merged view)
    work = excel_df.copy()
 
    # Resolve a final ISO2: manual wins -> then existing/auto -> else None (to be enriched)
    # Priority:
    #   1) HQ_ISO2_manual (Excel manual)
    #   2) HQ_ISO2 (Excel auto column if present)
    #   3) inst_canon_ctry_hq from Mongo (already merged above into HQ_ISO2 if empty)
    work["HQ_ISO2_final"] = work["HQ_ISO2_manual"]
    work["HQ_ISO2_final"] = work["HQ_ISO2_final"].where(work["HQ_ISO2_final"].notna(), work["HQ_ISO2"])
    # Now enrich only rows still missing HQ_ISO2_final
    need_enrichment_idx = work.index[work["HQ_ISO2_final"].isna()]
 
    enriched_count = 0
    manual_applied = work["HQ_ISO2_manual"].notna().sum()
 
    if do_enrich and len(need_enrichment_idx) > 0:
        print(f"🌍 Enriching {len(need_enrichment_idx)} companies (missing ISO2 only)...")
        for i in tqdm(need_enrichment_idx, desc="Enrichment"):
            row = work.loc[i]
            name_for_lookup = row["Name_manual"] if pd.notna(row["Name_manual"]) and str(row["Name_manual"]).strip() else row["inst_canon"]
 
            country_full = get_headquarters_country(str(name_for_lookup))
            if country_full:
                iso2 = country_to_iso2(country_full)
                work.at[i, "HQ_country"] = country_full
                work.at[i, "HQ_ISO2_final"] = iso2
                work.at[i, "HQ_ISO2"] = iso2  # keep Excel auto column in sync
                work.at[i, "HQ_region"] = iso2_to_region(iso2)
                enriched_count += 1
            else:
                # leave as NaN if no match
                pass
            time.sleep(SLEEP_BETWEEN_LOOKUPS_SEC)
    else:
        if do_enrich:
            print("✅ Nothing to enrich — all ISO2 values are present (manual or existing).")
        else:
            print("⏭️  Skipping enrichment (quick sync mode).")
 
    # Any rows where manual ISO2 is set: recompute country/region if not already provided
    rows_with_manual = work.index[work["HQ_ISO2_manual"].notna()]
    for i in rows_with_manual:
        iso2 = str(work.at[i, "HQ_ISO2_manual"]).upper()
        if pd.isna(work.at[i, "HQ_country"]) or not str(work.at[i, "HQ_country"]).strip():
            # We only have ISO2 — country name is optional; leave it if no resolver is available.
            # If you want to back-resolve country names from ISO2, you could add a small map here.
            pass
        work.at[i, "HQ_region"] = iso2_to_region(iso2)
        work.at[i, "HQ_ISO2_final"] = iso2
        work.at[i, "HQ_ISO2"] = iso2  # reflect into auto column for transparency
 
    # --------------------------
    # WRITE BACK TO MONGO
    # --------------------------
    coll = db[COLLECTION_NAME]
    updated_docs = 0
    skipped_docs_existing = 0
 
    # Build a lookup of current Mongo ISO2 to avoid unnecessary writes
    mongo_iso_lookup = df_mongo.set_index("inst_canon")["inst_canon_ctry_hq"].to_dict()
 
    for _, r in work.iterrows():
        canon = r["inst_canon"]
        final_iso2 = r.get("HQ_ISO2_final")
 
        # If no ISO2 at all, skip
        if pd.isna(final_iso2) or not str(final_iso2).strip():
            continue
 
        final_iso2 = str(final_iso2).upper()
        current_iso2 = mongo_iso_lookup.get(canon)
 
        # If Mongo already has same ISO2 and there's no manual change, skip
        if current_iso2 and str(current_iso2).upper() == final_iso2:
            skipped_docs_existing += 1
            continue
 
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
 
        res = coll.update_many({"inst_canon": canon}, {"$set": update})
        updated_docs += res.modified_count
 
    # --------------------------
    # SAVE/REFRESH EXCEL BUFFER
    # --------------------------
    # Keep only the human-friendly view in Excel
    excel_out = work[["inst_canon", "Name_manual", "HQ_ISO2", "HQ_ISO2_manual", "HQ_country", "HQ_region"]].copy()
    excel_out.sort_values("inst_canon", inplace=True, ignore_index=True)
    write_excel_safely(excel_out, OUTPUT_FILE)
 
    # --------------------------
    # SUMMARY
    # --------------------------
    total_inst = len(work)
    available_iso2 = work["HQ_ISO2_final"].notna().sum()
    print("\n📊 Summary")
    print(f"  Companies total:                {total_inst}")
    print(f"  Manual ISO2 applied:            {manual_applied}")
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