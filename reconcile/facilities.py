import pandas as pd
import sys; sys.path.append("..")
import logging
from mongo_client import mongo_client, facilities_collection, test_mongo_connection
from src.config import GRPD_PROJECTS_FILTER, FACILITIES
from src.facilities_helpers import bbox_to_geojson 
from src.vote_helpers import fill_single_product_lv2, parse_capacity_value

def write_facilities():
    test_mongo_connection()

    # Clear existing facilities before inserting new ones
    facilities_collection.delete_many({})
    logging.info("🗑️ Cleared existing facilities from MongoDB.")

    df = pd.read_excel(GRPD_PROJECTS_FILTER)
    logging.debug(df["bbox"].map(type).value_counts())
    logging.debug(df["bbox"].head().tolist())

    # Parse dates
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m", errors="coerce")
    df["_sort_date"] = df["date"].fillna(pd.Timestamp.max)

    # Normalize capacities
    df["capacity_normalized"] = df["capacity_normalized"].apply(parse_capacity_value)

    # Status categorization (optional — needed only if you plan further dedup by status)
    STATUS_ORDER = ["operational", "under construction", "announced", "unclear"]
    df["status"] = pd.Categorical(df["status"], categories=STATUS_ORDER, ordered=True)

    # ---- Facilities grouping ----
    df_facilities = df.groupby("cluster_id").agg({
        "inst_canon": "first",
        "iso2": "first",
        "adm1": "first",
        "bbox": "first",
        "product_lv1": "first",
        "product_lv2": "unique"
    }).reset_index()

    logging.info(f"Saving a copy of facilities to Excel at {FACILITIES}")
    df_facilities.to_excel(FACILITIES)

    # ---- Capacities deduplication ----
    df1 = (
        df.sort_values(["cluster_id", "date"], ascending=[True, True], na_position="last")
          .drop_duplicates(["cluster_id", "capacity_normalized", "status", "phase"], keep="first")
    )

    def pandas_row_to_capacity(row):
        return {
            "amount": row["capacity_normalized"],
            "status": row["status"] if pd.notna(row["status"]) else None,
            "phase": row["phase"] if pd.notna(row["phase"]) else None,
            "date": row["date"].strftime("%Y-%m-%d") if pd.notna(row["date"]) else None,
            # ADD LOGIC to also store product_lv2 as a dictionary within capacities (for cases where capacity does not apply to full facility)
            "articleID": row["article_id"] if pd.notna(row["article_id"]) else None
        }

    capacity_dict = (
        df1.groupby("cluster_id")
           .apply(lambda g: [pandas_row_to_capacity(r) for _, r in g.iterrows()])
           .to_dict()
    )

    logging.info(f"Number of raw capacities - {len(df)}")
    logging.info(f"📅 Unique capacities remaining after deduplication (keeping earliest date): {len(df1)}")

    # convert DataFrame to MongoDB documents
    facilities_documents = []
    for _, row in df_facilities.iterrows():
        cluster_id = row["cluster_id"]

        # filter out NaN values from product_lv2 - assuming for now all product_lv2 applies....
        product_lv2_list = list(row["product_lv2"]) if pd.notna(row["product_lv2"]).any() else []
        product_lv2_clean = [item for item in product_lv2_list if pd.notna(item)]

        # convert bbox to GeoJSON format
        bbox_geojson = bbox_to_geojson(row["bbox"]) if pd.notna(row["bbox"]) else None

        mongo_entry = {
            "cluster_id": row["cluster_id"],
            "inst_canon": row["inst_canon"] if pd.notna(row["inst_canon"]) else None,
            "iso2": row["iso2"] if pd.notna(row["iso2"]) else None,
            "adm1": row["adm1"] if pd.notna(row["adm1"]) else None,
            "bbox": row["bbox"] if pd.notna(row["bbox"]) else None,
            "bbox_geojson": bbox_geojson,
            "product_lv1": row["product_lv1"] if pd.notna(row["product_lv1"]) else None,
            "product_lv2": product_lv2_clean,
            "capacities": capacity_dict.get(cluster_id, [])
        }
        facilities_documents.append(mongo_entry)

    # insert all documents into MongoDB
    if facilities_documents:
        facilities_collection.insert_many(facilities_documents)
        logging.info(f"✅ Inserted {len(facilities_documents)} facilities into MongoDB, with {len(df1)} capacities.")
    else:
        logging.warning("⚠️ No facilities to insert into MongoDB.") 