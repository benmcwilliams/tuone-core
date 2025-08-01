import logging
import time
from src.logger import setup_logger
from normalise_products import classify_products_sync_mongo
from normalise_owners import clean_owner_names
from query_geonames import query_geonames_new_cities
from flatten import run_flatten_articles
from merge import merge_nodes_rels
from group import group_projects

def main(update_mongo_metadata=False):

    t0_pipeline = time.time()
    setup_logger()
    logging.info(f"Updating mongo-metadata is set to {update_mongo_metadata}")

    if update_mongo_metadata:

        logging.info("🕴️Normalising companies...")
        clean_owner_names()

        logging.info("🌎 Querying geonames...")
        query_geonames_new_cities()

        logging.info("🧸 Classifying products")
        classify_products_sync_mongo()

    logging.info("🗞️ Flattening articles...")
    run_flatten_articles()

    logging.info("🉑 Merging nodes and relationships...")
    merge_nodes_rels()

    logging.info("🧮 Grouping projects...")
    group_projects()

    # final timing
    t1_pipeline = time.time()
    logging.info(f"Total pipeline time: {(t1_pipeline - t0_pipeline)/60:.2f} minutes")

if __name__ == "__main__":
    main(update_mongo_metadata=False)