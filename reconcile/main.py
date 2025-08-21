import logging
import time
from src.logger import setup_logger
from normalise_products import classify_products_sync_mongo
from normalise_owners import clean_owner_names
from query_geonames import query_geonames_new_cities
from flatten import run_flatten_articles
from merge import merge_nodes_rels
from normalise_capacity import run_capacity_normalisation_pipeline
from group import group_projects
from facilities import write_facilities
from phase_summary import determine_phase_summary
from project_page import output_capacities_plot

def main(update_mongo_metadata=False):

    t0_pipeline = time.time()
    setup_logger()
    logging.info(f"Updating mongo-metadata is set to {update_mongo_metadata}")

    if update_mongo_metadata:

        logging.info("🕴️Normalising companies...")          # only updates nodes with missing name_canon
        clean_owner_names()

        logging.info("🌎 Querying geonames...")
        query_geonames_new_cities(limit=18000,skip=0)

        logging.info("🧸 Classifying products")             # re-updates all products
        classify_products_sync_mongo()

    logging.info("🗞️ Flattening articles...")
    run_flatten_articles()

    logging.info("🉑 Merging nodes and relationships...")
    merge_nodes_rels()

    logging.info("Normalising capacities")
    run_capacity_normalisation_pipeline()

    # run_investment_normalisation_pipeline()

    logging.info("🫂 Grouping projects...")
    group_projects()

    logging.info("🏭 Importing facilities")
    write_facilities()

    logging.info("🧮 Determining phase summaries")
    determine_phase_summary()

    logging.info("Outputting clean capacities summary data")
    output_capacities_plot()

    # final timing
    t1_pipeline = time.time()
    logging.info(f"Total pipeline time: {(t1_pipeline - t0_pipeline)/60:.2f} minutes")

if __name__ == "__main__":
    main(update_mongo_metadata=False)