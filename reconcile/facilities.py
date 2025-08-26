import pandas as pd
import numpy as np
import sys; sys.path.append("..")
import logging
from mongo_client import facilities_collection, test_mongo_connection
from src.config import FACILITIES, GROUPED_CAPACITIES, GROUPED_FACTORIES, ZEV_PRODUCTION
from src.facilities_helpers import parse_capacity_value, canon_pl2

STATUS_ORDER = ["operational", "under construction", "announced", "unclear"]

def write_facilities():

    test_mongo_connection()

    # fresh collection
    facilities_collection.delete_many({})
    logging.info("🗑️ Cleared existing facilities from MongoDB.")

    # =========================
    # A) Facilities (from GROUPED_FACTORIES)
    # =========================

    df = pd.read_excel(GROUPED_FACTORIES)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m", errors="coerce")

    # return latest non-null facility_status + its date per project_id
    latest_status = (
        df.loc[df["factory_status"].notna(), ["project_id", "factory_status", "date"]]
        .sort_values(["project_id", "date"])
        .groupby("project_id", as_index=False)
        .tail(1)                                  # newest per project_id
        .rename(columns={"date": "factory_status_date"})
    )

    # facility-level grouping
    df_facilities = (
        df.groupby("project_id").agg({
            "inst_canon": "first",
            "iso2": "first",
            "adm1": "first",
            "lat": "first",
            "lon": "first",
            "product_lv1": "first",
            "product_lv2": "unique",
        }).reset_index()
    )

    # attach latest status + date
    df_facilities = df_facilities.merge(latest_status, on="project_id", how="left")

    # optional (save an excel snapshot)
    logging.info(f"Saving a copy of facilities to Excel at {FACILITIES}")
    df_facilities.to_excel(FACILITIES, index=False)

    # =========================
    # B) Capacities (from GROUPED_CAPACITIES)
    # =========================

    # --- CONCAT ---
    df_cap = pd.read_excel(GROUPED_CAPACITIES)
    df_zev = pd.read_excel(ZEV_PRODUCTION)
    df_cap = pd.concat([df_cap, df_zev], ignore_index=True)

    # normalize + parse
    df_cap["date"] = pd.to_datetime(df_cap["date"], errors="coerce")
    # we dropped date time format="%Y-%m to ensure match with df_zev (CHECK OKAY)
    df_cap["capacity_normalized"] = df_cap["capacity_normalized"].apply(parse_capacity_value)
    df_cap["status"] = pd.Categorical(df_cap["status"], categories=STATUS_ORDER, ordered=True)

    # normalize/hash product_lv2 for use as a dedup key
    df_cap["pl2_key"] = df_cap["product_lv2"].apply(canon_pl2)

    # ---- Capacities deduplication ----
    df_cap_dedup = (
        df_cap
        # 1. sort rows per project chronologically
        .sort_values(["project_id", "date"], ascending=[True, True], na_position="last")
        
        # 2. drop exact duplicate rows defined by (project_id, capacity, status, phase, pl2_key)
        #    → keep only the first (earliest) mention of each unique combo
        .drop_duplicates(["project_id", "capacity_normalized", "status", "phase", "pl2_key"], 
                         keep="first")
    )

    # group capacities by the same product_lv1, amount, status & phase. 
    # so this would create two entries for battery / vehicle, but only one entry for fossil / electric 
    # we could then apply here the filter? 

    # --- Group identical capacities that only differ by product_lv2 ---
    group_keys = ["project_id", "product_lv1", "capacity_normalized", "status", "phase"]

    # union product_lv2 via pl2_key (which is a tuple of unique values)
    df_cap_grouped_lv2 = (
        df_cap_dedup
        .groupby(group_keys, dropna=False, sort=False, observed=True)
        .agg(
            pl2_union=("pl2_key", lambda T: tuple(sorted({v for tup in T for v in tup}))),
            date=("date","first"),
            article_id=("article_id","first"))
        .reset_index()
        .rename(columns={"pl2_union": "product_lv2"})
    )

    # --- Logging / debug checks ---
    logging.info("Capacities: raw=%d", len(df_cap))
    logging.info("Capacities: dedup=%d | grouped=%d", len(df_cap_dedup), len(df_cap_grouped_lv2))

    logging.info("Sample grouped capacities (5):\n%s",
                df_cap_grouped_lv2.head(5)[
                    ["project_id","product_lv1","capacity_normalized","status","phase","date","article_id","product_lv2"]
                ].to_string(index=False))

    from collections import Counter
    _applies = Counter(df_cap_grouped_lv2["product_lv2"].apply(lambda pl2: (
        "electric" if "electric" in set(pl2) and "fossil" not in set(pl2)
        else "fossil" if "fossil" in set(pl2) and "electric" not in set(pl2)
        else "mix"
    )))
    logging.info("applies_to distribution: %s", dict(_applies))

    def classify_pl2_applies_to(pl2_values):
        s = {str(v).strip().lower() for v in pl2_values if pd.notna(v)}
        has_e = "electric" in s
        has_f = "fossil" in s
        if has_e and not has_f: return "electric"
        if has_f and not has_e: return "fossil"
        return "mix"

    def row_to_capacity(r):
        pl2 = list(r["product_lv2"])
        return {
            "amount": r["capacity_normalized"],
            "status": r["status"] if pd.notna(r["status"]) else None,
            "phase":  r["phase"] if pd.notna(r["phase"]) else None,
            "product_lv2": pl2,
            "applies_to": classify_pl2_applies_to(pl2),
            "date":   r["date"].strftime("%Y-%m-%d") if pd.notna(r["date"]) else None,
            "articleID": r["article_id"] if pd.notna(r["article_id"]) else None,
        }

    # --- Build capacity dict ---
    capacity_dict = (
        df_cap_grouped_lv2.groupby("project_id")
           .apply(lambda g: [row_to_capacity(r) for _, r in g.iterrows()])
           .to_dict()
    )

    logging.info(f"Number of raw capacities: {len(df_cap)}")
    logging.info(f"📅 Unique capacities after dedup (earliest per tuple): {len(df_cap_dedup)}")

    # =========================
    # C) Build Mongo documents (facilities + attached capacities)
    # =========================

    # # convert DataFrame to MongoDB documents
    facilities_documents = []
    num_with_caps = 0
    num_without_caps = 0     # skipped non-vehicle with no caps
    num_vehicle_with_caps = 0
    num_vehicle_without_caps = 0

    pre_total = len(df_facilities)

    for _, row in df_facilities.iterrows():

        # logic which does not write facilities without capacities UNLESS they are vehicle manufacturing
        project_id = row["project_id"]
        is_vehicle = (row["product_lv1"] == "vehicle")

        caps = capacity_dict.get(project_id, [])

        if caps:
            num_with_caps += 1
            if is_vehicle:
                num_vehicle_with_caps += 1
        else:
            if is_vehicle:
                # keep (don’t skip), but count as vehicle-without-caps
                num_vehicle_without_caps += 1
            else:
                # skip non-vehicle facilities with no capacities
                num_without_caps += 1
                continue

        # clean product_lv2 (ensure list of non-nulls)
        vals = row["product_lv2"]
        product_lv2_clean = [v for v in np.atleast_1d(vals) if pd.notna(v)]

        # latest facility status (string date is fine for now; you can store BSON datetime later)
        latest_status_obj = None
        if pd.notna(row.get("factory_status")) or pd.notna(row.get("factory_status_date")):
            latest_status_obj = {
                "status": row.get("factory_status"),
                "date": row.get("factory_status_date").strftime("%Y-%m-%d") if pd.notna(row.get("factory_status_date")) else None,
            }

        doc = {
            "project_id": project_id,
            "inst_canon": row["inst_canon"] if pd.notna(row["inst_canon"]) else None,
            "iso2": row["iso2"] if pd.notna(row["iso2"]) else None,
            "adm1": row["adm1"] if pd.notna(row["adm1"]) else None,
            "lat": row["lat"] if pd.notna(row["lat"]) else None,
            "lon": row["lon"] if pd.notna(row["lon"]) else None,
            "product_lv1": row["product_lv1"] if pd.notna(row["product_lv1"]) else None,
            "product_lv2": product_lv2_clean,
            "latest_factory_status": latest_status_obj or {"status": None, "date": None},
            "capacities": capacity_dict.get(project_id, []),
        }
        facilities_documents.append(doc)

    # Logging summary of the guardrail (no caps) effect
    logging.info(
        "Facilities before filter: %d | inserted with capacities: %d | "
        "skipped (non-vehicle, no capacities): %d | vehicles with caps: %d | "
        "vehicles without caps (inserted): %d",
        pre_total, num_with_caps, num_without_caps,
        num_vehicle_with_caps, num_vehicle_without_caps
    )

    if facilities_documents:
        facilities_collection.insert_many(facilities_documents)
        logging.info(f"✅ Inserted {len(facilities_documents)} facilities into MongoDB "
                     f"with {len(df_cap_dedup)} deduplicated capacities attached.")
    else:
        logging.warning("⚠️ No facilities to insert into MongoDB.")

if __name__ == "__main__":
    write_facilities()