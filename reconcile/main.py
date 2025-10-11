import sys; sys.path.append("..")
import logging
import time
from mongo_client import facilities_collection
from src.main_helpers import log_nodes_for_article
from src.logger import setup_logger
from src.merge_helpers import make_context_from_frames
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
from assign_phase import assign_phase_num
from phase_summary import compute_summaries

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

debug_articleID = "68e67fbf2423d7d8b125bfc0"

def main(update_mongo_metadata=False, update_main_database=False):

    t0_pipeline = time.time()
    setup_logger()
    logging.info(f"Updating mongo-metadata is set to {update_mongo_metadata}")

    if update_mongo_metadata:

        logging.info("🕴️Normalising companies...")  # only updates nodes with missing name_canon (inst_canon)
        clean_owner_names()

        #logging.info("🌎 Querying geonames...") 
        query_geonames_new_cities(limit=21000, skip=0, failure_backoff_days=2000)

        # logging.info("🧸 Classifying products")             # re-updates all products
        # classify_products_sync_mongo()

    if update_main_database:

        logging.info("🗞️ Flattening articles...")
        nodes_df, rels_df = run_flatten_articles(save=True)

        logging.info("🔗 Building context in-memory...")
        ctx = make_context_from_frames(nodes_df, rels_df)
        log_nodes_for_article(ctx, debug_articleID)

        logging.info("🉑 Merging nodes and relationships...")
        df_capacity =   run_view(FACTORY_TECH_SPEC,           FACTORY_TECH,         context=ctx)  # capacity-centric
        df_jv =         run_view(COMPANY_FORMS_JV_SPEC,       COMPANY_JV,           context=ctx)  # JV directory
        df_investment = run_view(INVESTMENT_FUNDS_SPEC,       INVESTMENT_FUNDS,     context=ctx)  # investment-centric
        df_facility =   build_registry_union(to_excel=True,                         context=ctx)  # facility directory

        logging.info("- - - Normalising capacities")
        df_clean_caps = run_capacity_normalisation_pipeline(df_in=df_capacity,
                                              write_debug=False,
                                              write_outputs=True)

        logging.info("- - - Normalising investments")
        df_clean_caps_invs = run_investment_normalisation_pipeline(df_in=df_clean_caps,
            output_path = FACTORY_TECH_CLEAN_CAPACITIES_INVESTMENTS, 
            write_outputs=True, write_check=False)

        df_clean_invs = run_investment_normalisation_pipeline(df_in=df_investment, 
        output_path = CLEAN_INVESTMENT_FUNDS, write_outputs=True, write_check=True)

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
    assign_phase_num(dry_run=False,
                        limit=None,
                        query={})

    compute_summaries()
    logging.info(f"✅ Phase summaries computed.")


    # final timing
    t1_pipeline = time.time()
    logging.info(f"Total pipeline time: {(t1_pipeline - t0_pipeline)/60:.2f} minutes")

if __name__ == "__main__":
    main(update_mongo_metadata=True,
        update_main_database=True)
