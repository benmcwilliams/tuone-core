import pandas as pd
import sys; sys.path.append("..")
import logging
from mongo_client import mongo_client, facilities_collection
from src.config import GRPD_PROJECTS_FILTER, FACILITIES

def bbox_to_geojson(bbox_dict):
    """Convert bbox dictionary to GeoJSON Polygon format"""
    if not bbox_dict or not isinstance(bbox_dict, dict):
        return None
    
    return {
        "type": "Polygon",
        "coordinates": [[
            [bbox_dict["west"], bbox_dict["south"]],
            [bbox_dict["east"], bbox_dict["south"]],
            [bbox_dict["east"], bbox_dict["north"]],
            [bbox_dict["west"], bbox_dict["north"]],
            [bbox_dict["west"], bbox_dict["south"]]
        ]]
    }

def write_facilities():
    try:
        mongo_client.admin.command("ping")
        print("✅ Connected to MongoDB Atlas!")
    except Exception as e:
        print(f"❌ MongoDB Connection Error: {e}")
        raise

    # Clear existing facilities before inserting new ones
    facilities_collection.delete_many({})
    logging.info("🗑️ Cleared existing facilities from MongoDB.")

    df = pd.read_excel(GRPD_PROJECTS_FILTER)
    logging.info(df["bbox"].map(type).value_counts())
    logging.info(df["bbox"].head().tolist())

    df_facilities = df.groupby("cluster_id").agg({
        "inst_canon": "first",
        "iso2": "first",
        "adm1": "first",
        "bbox": "first",
        "product_lv1": "first",
        "product_lv2": "unique"
    }).reset_index()

    logging.info(f"Saving a copy of facilities to excel at {FACILITIES}")
    df_facilities.to_excel(FACILITIES)

    # convert DataFrame to MongoDB documents
    facilities_documents = []
    for _, row in df_facilities.iterrows():

        # filter out NaN values from product_lv2
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
            "product_lv2": product_lv2_clean
        }
        facilities_documents.append(mongo_entry)

    # insert all documents into MongoDB
    if facilities_documents:
        facilities_collection.insert_many(facilities_documents)
        logging.info(f"✅ Inserted {len(facilities_documents)} facilities into MongoDB.")
    else:
        logging.warning("⚠️ No facilities to insert into MongoDB.") 