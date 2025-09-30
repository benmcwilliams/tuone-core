import sys; sys.path.append("..")
import logging
import time
from mongo_client import facilities_collection
from src.logger import setup_logger
from normalise_products import classify_products_sync_mongo
from normalise_owners import clean_owner_names
from query_geonames import query_geonames_new_cities
from flatten import run_flatten_articles
from merge import run_view
from normalise_capacity import run_capacity_normalisation_pipeline
from normalise_investment import run_investment_normalisation_pipeline
from registry_union import build_registry_union
from group import group_projects
from facilities import write_facilities
from attach_events import attach_events
from assign_phase import process_documents
from phase_summary import compute_summaries
from project_page import output_plots

from src.merge_specifications import (
    FACTORY_TECH_SPEC,
    COMPANY_FORMS_JV_SPEC,
    INVESTMENT_FUNDS_SPEC,
)
from src.config import (
    GROUP_SPEC,
    FACTORY_TECH,
    INVESTMENT_FUNDS,
    COMPANY_JV,
    FACTORY_TECH_CLEAN_CAPACITIES,
    FACTORY_TECH_CLEAN_CAPACITIES_INVESTMENTS,
    CLEAN_INVESTMENT_FUNDS,
)

def main(update_mongo_metadata=False, update_main_database=False):

    t0_pipeline = time.time()
    setup_logger()
    logging.info(f"Updating mongo-metadata is set to {update_mongo_metadata}")

    if update_mongo_metadata:

        logging.info(
            "🕴️Normalising companies..."
        )  # only updates nodes with missing name_canon
        clean_owner_names()

        #logging.info("🌎 Querying geonames...")
        #query_geonames_new_cities(limit=20000, skip=0)

        # logging.info("🧸 Classifying products")             # re-updates all products
        # classify_products_sync_mongo()

    if update_main_database:

        logging.info("🗞️ Flattening articles...")
        run_flatten_articles()

        logging.info("🉑 Merging nodes and relationships...")
        logging.info("- - - FACTORY_TECH_SPEC")
        run_view(FACTORY_TECH_SPEC, FACTORY_TECH)  # capacity centric
        logging.info("- - - COMPANY_JV_SPEC")
        run_view(COMPANY_FORMS_JV_SPEC, COMPANY_JV)
        logging.info("- - - INVESTMENT_FUNDS_SPEC")
        run_view(INVESTMENT_FUNDS_SPEC, INVESTMENT_FUNDS)  # investment centric

        logging.info("🏭 Building registry union (direct + capacity + investment)…")
        build_registry_union(to_excel=True)  # writes FACTORY_REGISTRY for grouping

        logging.info("Normalising capacities")
        run_capacity_normalisation_pipeline()

        logging.info("Normalising investments")
        run_investment_normalisation_pipeline(
            FACTORY_TECH_CLEAN_CAPACITIES, FACTORY_TECH_CLEAN_CAPACITIES_INVESTMENTS
        )
        run_investment_normalisation_pipeline(INVESTMENT_FUNDS, CLEAN_INVESTMENT_FUNDS)

        logging.info("🫂 Grouping projects...")
        for in_path, out_path, output_cols in GROUP_SPEC:
            print(in_path)
            logging.info(f"Processing: {in_path} → {out_path}")
            group_projects(in_path, out_path, output_cols)

    logging.info("🏭 Importing facilities")
    write_facilities()  # this updates only iso2 | adm1 | inst_canon | product_lv1 hexspaceID facilities

    logging.info("📅 Assigning events to facilities")
    attach_events()

    logging.info("🔢 Assigning phase number")
    process_documents(dry_run=False,
                        limit=None,
                        query={})

    compute_summaries()
    logging.info(f"✅ Phase summaries computed.")

    # logging.info("Outputting clean capacities summary data")
    output_plots()

    # final timing
    t1_pipeline = time.time()
    logging.info(f"Total pipeline time: {(t1_pipeline - t0_pipeline)/60:.2f} minutes")

if __name__ == "__main__":
    main(update_mongo_metadata=True,
        update_main_database=True)
