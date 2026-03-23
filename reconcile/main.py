import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

import logging
import time
from src.main_helpers import log_nodes_for_article
from src.logger import setup_logger, setup_article_debug_logger, get_article_debug_log_path
from src.debug_helpers import DebugArticleTracker, set_debug_tracker, get_debug_tracker

from src.merge_specifications import (
    FACTORY_TECH_SPEC,
    COMPANY_FORMS_JV_SPEC,
    INVESTMENT_FUNDS_SPEC,
)
from src.config import (
    GROUPED_CAPACITIES,
    GROUPED_FACTORIES,
    GROUPED_INVESTMENTS,
    grouped_capacities_cols,
    grouped_facilities_cols,
    grouped_investments_cols,
)

# functions to update mongo metadata
from normalise_owners import clean_owner_names
from query_geonames import query_geonames_new_cities

# functions to update main database 
from ev_volumes import build_zev_og_clean_excel
from flatten import run_flatten_articles
from src.merge_helpers import make_context_from_frames
from merge import run_view
from registry_union import build_registry_union
from normalise_capacity import run_capacity_normalisation_pipeline
from normalise_investment import run_investment_normalisation_pipeline
from group import group_projects

# functions to update our mongodb database
from facilities import write_facilities
from attach_events import attach_events
from assign_phase import assign_phase_num
from phase_summary import compute_summaries
from sync_inst_canon_opensource import sync_inst_canon_to_opensourcedev

# --- Verbose / debug (set True to enable noisier logs) ---
VERBOSE_INVESTMENT_SPLIT = False
VERBOSE_ATTACH_EVENTS_MISSING_PIDS = False
VERBOSE_FLATTEN = False
VERBOSE_GROUPING = False
VERBOSE_CAPACITY = False
VERBOSE_GEONAMES = False


def main(
    update_mongo_metadata: bool = False,
    update_main_database: bool = False,
    debug_article_id: str | None = None,
):

    t0_pipeline = time.time()
    setup_logger()

    # Per-article debug: write to logs/articleID/{article_id}.log only; main output gets one pointer line
    if debug_article_id:
        article_logger = setup_article_debug_logger(debug_article_id)
        if article_logger:
            set_debug_tracker(DebugArticleTracker(debug_article_id, article_logger))
            log_path = get_article_debug_log_path(debug_article_id)
            logging.info("Debug output for article %s written to: %s", debug_article_id, log_path)

    logging.info(f"Updating mongo-metadata is set to {update_mongo_metadata}")

    if update_mongo_metadata:

        logging.info("🕴️Normalising companies...")  # only updates nodes with missing name_canon (inst_canon)
        clean_owner_names()

        logging.info("🌎 Querying geonames...") 
        query_geonames_new_cities(limit=22000, skip=0, failure_backoff_days=2000, verbose=VERBOSE_GEONAMES)

        # logging.info("🧸 Classifying products")             # re-updates all products
        # classify_products_sync_mongo()

    if update_main_database:

        logging.info("Update EV Volumes data")
        df_zev = build_zev_og_clean_excel(to_excel=False)

        # read in IEA hydrogen database

        logging.info("🗞️ Flattening articles...")
        nodes_df, rels_df = run_flatten_articles(save=False, debug_article_id=debug_article_id, verbose=VERBOSE_FLATTEN)

        logging.info("🔗 Building context in-memory...")
        ctx = make_context_from_frames(nodes_df, rels_df)
        if debug_article_id:
            log_nodes_for_article(ctx, debug_article_id)

        logging.info("🉑 Merging nodes and relationships...")
        df_capacity =   run_view(FACTORY_TECH_SPEC,           out_path=None, context=ctx, view_name="FACTORY_TECH_SPEC")
        df_jv =         run_view(COMPANY_FORMS_JV_SPEC,       out_path=None, context=ctx, view_name="COMPANY_FORMS_JV_SPEC")
        df_investment = run_view(INVESTMENT_FUNDS_SPEC,       out_path=None, context=ctx, view_name="INVESTMENT_FUNDS_SPEC")
        df_facility =   build_registry_union(to_excel=False, context=ctx, debug_article_id=debug_article_id)  # facility directory

        logging.info("- - - Normalising capacities")
        df_clean_caps = run_capacity_normalisation_pipeline(df_in=df_capacity,
                                              write_debug=False,
                                              write_outputs=False,
                                              verbose=VERBOSE_CAPACITY)

        logging.info("- - - Normalising investments")
        df_clean_caps_invs = run_investment_normalisation_pipeline(df_in=df_clean_caps,
            output_path=None,
            write_outputs=False,
            write_check=False,
            verbose_investment_split=VERBOSE_INVESTMENT_SPLIT)

        df_clean_invs = run_investment_normalisation_pipeline(df_in=df_investment,
        output_path=None,
        write_outputs=False,
        write_check=True,
        verbose_investment_split=VERBOSE_INVESTMENT_SPLIT)

        logging.info("🫂 Grouping projects...")
        if VERBOSE_GROUPING:
            print(GROUPED_CAPACITIES)
        logging.info(f"Processing: capacities → {GROUPED_CAPACITIES}")
        group_projects(df_clean_caps_invs, GROUPED_CAPACITIES, grouped_capacities_cols, debug_article_id=debug_article_id)
        if VERBOSE_GROUPING:
            print(GROUPED_FACTORIES)
        logging.info(f"Processing: factories → {GROUPED_FACTORIES}")
        df_grouped_factories = group_projects(df_facility, GROUPED_FACTORIES, grouped_facilities_cols, debug_article_id=debug_article_id)
        if VERBOSE_GROUPING:
            print(GROUPED_INVESTMENTS)
        logging.info(f"Processing: investments → {GROUPED_INVESTMENTS}")
        group_projects(df_clean_invs, GROUPED_INVESTMENTS, grouped_investments_cols, debug_article_id=debug_article_id)

    logging.info("🏭 Importing facilities")
    if update_main_database:
        write_facilities(grouped_factories_df=df_grouped_factories, zev_df=df_zev)
    else:
        write_facilities()

    logging.info("📅 Assigning events to facilities")
    attach_events(debug_article_id=debug_article_id, verbose_missing_pids=VERBOSE_ATTACH_EVENTS_MISSING_PIDS)

    logging.info("🔢 Assigning phase number")
    assign_phase_num(dry_run=False,
                        limit=None,
                        query={})

    compute_summaries()
    logging.info(f"✅ Phase summaries computed.")

    logging.info("🔁 Syncing inst_canon to opensourcedev")
    sync_inst_canon_to_opensourcedev()

    # final timing
    t1_pipeline = time.time()
    logging.info(f"Total pipeline time: {(t1_pipeline - t0_pipeline)/60:.2f} minutes")

    # Per-article debug: write diagnosis summary to article log file and clear tracker
    tracker = get_debug_tracker()
    if tracker is not None:
        tracker.section("Diagnosis summary")
        bullets = tracker.get_diagnosis_bullets()
        if bullets:
            for b in bullets:
                tracker.info("  • %s", b)
            tracker.info("")
            tracker.info("Next checks: ensure article has ownership (owns) edges for EU factories, or that facility locations resolve to EU countries (iso2 in EUROPEAN_COUNTRIES).")
        else:
            tracker.info("No drop reasons recorded; article may have contributed rows to one or more outputs.")
        set_debug_tracker(None)

if __name__ == "__main__":
    main(
        update_mongo_metadata=True,
        update_main_database=True,
        debug_article_id="69a6f19e721a5d192a8320d0",
    )
