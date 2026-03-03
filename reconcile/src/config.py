# config.py

from pathlib import Path

# Reconcile root (reconcile/) so paths work from project root or from reconcile/
_RECONCILE_ROOT = Path(__file__).resolve().parent.parent


def _p(path: str) -> str:
    """Resolve storage paths relative to reconcile root."""
    p = path.lstrip("./")
    return str(_RECONCILE_ROOT / p)


# Mongo query to filter articles to process (must have nodes & relationships)
# optional filter for meta.category.
ARTICLE_QUERY = {
    "nodes": {"$exists": True},
    "relationships": {"$exists": True},
    "meta.category": {"$in": ["user", "user_text", "electrive", "justauto", "pvmagazine", "pvtech", "world_energy",
                                "offshorewind", "renewsBiz"]}
}

ARTICLE_PROJECTION = {
    "_id": 1,
    "nodes": 1,
    "relationships": 1
}

# builder files
ALL_NODES = _p("storage/output/all_nodes.xlsx")
ALL_RELS = _p("storage/output/all_rels.xlsx")
GEO_LOOKUP_JSON = _p("storage/output/geo_lookup.json")

# raw views
FACTORY_REGISTRY = _p("storage/output/factory_registry.xlsx")
FACTORY_TECH = _p("storage/output/factory-technological.xlsx")
COMPANY_JV = _p("storage/output/company-joint-venture.xlsx")
INVESTMENT_FUNDS = _p("storage/output/investment-funds-factory.xlsx")

# cleaning capacities and investments
FACTORY_TECH_CLEAN_CAPACITIES = _p("storage/output/factory-technological-clean-capacities.xlsx")
FACTORY_TECH_CLEAN_CAPACITIES_INVESTMENTS = _p("storage/output/factory-technological-clean-capacities-investments.xlsx")
CLEAN_INVESTMENT_FUNDS = _p("storage/output/clean-investment-funds-factory.xlsx")
CHECK_INVESTMENTS = _p("storage/output/check_investments.xlsx")
CAPACITIES_DEBUG = _p("storage/output/capacities-debug.xlsx")

# grouping
GROUPED_CAPACITIES = _p("storage/output/grouped-capacities.xlsx")
GROUPED_FACTORIES = _p("storage/output/grouped-factories.xlsx")
GROUPED_INVESTMENTS = _p("storage/output/grouped-investments.xlsx")
VEHICLES_IMPUTE = _p("storage/input/vehicles_impute.xlsx")
ZEV_PRODUCTION = _p("storage/input/zev_og_clean.xlsx")

GRPD_PROJECTS = _p("storage/output/all_projects.xlsx")
GRPD_PROJECTS_FILTER = _p("storage/output/filtered_projects.xlsx")
PRODUCT_CLASSIFICATION = _p("storage/input/product_classification.xlsx")
FACILITIES = _p("storage/output/facilities.xlsx")
CAPACITIES_PLOT = _p("storage/output/capacities_plot.xlsx")
BRUEGEL_IM = _p("storage/output/bruegel_investment_monitor.xlsx")

grouped_facilities_cols = [
    "inst_canon", "inst_type", "iso2", "factory", "admin_group_key",
    "product", "product_lv1", "product_lv2", "product_lv3", "factory_status", "date", 
    "project_id", "project_key_str", 
    "lat", "lon", "city_key", "adm1", "adm2", "adm3", "adm4",
    "article_id"
]

grouped_capacities_cols = [
    "inst_canon", "inst_type", "iso2", "factory", "admin_group_key",
    "product", "product_lv1", "product_lv2", "product_lv3", "factory_status", "date",
    "capacity", "capacity_normalized", "capacity_metric_normalized", "phase", "status", "additional", "capacity_id", 
    "project_id", "project_key_str", "vehicle_touches",
    "investment", "amount_EUR", "amount_EUR_2023_ameco_pvgd",
    "investment_status", "investment_phase", "is_total", 
    "lat", "lon", "city_key", "adm1", "adm2", "adm3", "adm4",
    "article_id", "investment_id"
]

grouped_investments_cols = [
    "inst_canon", "inst_type", "iso2", "factory", "admin_group_key",
    "product", "product_lv1", "product_lv2", "product_lv3", "factory_status", "date",
    "investment", "amount_EUR", "amount_EUR_2023_ameco_pvgd",
    "phase", "status", "is_total",
    "project_id", "project_key_str",
    "lat", "lon", "city_key", "adm1", "adm2", "adm3", "adm4", 
    "article_id", "investment_id"
]

GROUP_SPEC = [
        # (input_excel, output_excel, output_cols)
        (FACTORY_TECH_CLEAN_CAPACITIES_INVESTMENTS, GROUPED_CAPACITIES, grouped_capacities_cols),
        (FACTORY_REGISTRY,  GROUPED_FACTORIES, grouped_facilities_cols),
        (CLEAN_INVESTMENT_FUNDS, GROUPED_INVESTMENTS, grouped_investments_cols)
    ]