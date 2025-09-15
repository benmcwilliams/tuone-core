# config.py

# Mongo query to filter articles to process (must have nodes & relationships)
# optional filter for meta.category.
ARTICLE_QUERY = {
    "nodes": {"$exists": True},
    "relationships": {"$exists": True}
    #"meta.category": {"$in": ["electrive", "pvtech", "pvmagazine", "world_energy"]}
}

ARTICLE_PROJECTION = {
    "_id": 1,
    "nodes": 1,
    "relationships": 1
}

ALL_NODES = "storage/output/all_nodes.xlsx"
ALL_RELS = "storage/output/all_rels.xlsx"
FACTORY_REGISTRY = "storage/output/factory_registry.xlsx"
FACTORY_TECH = "storage/output/factory-technological.xlsx"
COMPANY_JV = "storage/output/company-joint-venture.xlsx"
INVESTMENT_FUNDS = "storage/output/investment-funds-factory.xlsx"

FACTORY_TECH_CLEAN_CAPACITIES = "storage/output/factory-technological-clean-capacities.xlsx"
CAPACITIES_DEBUG = "storage/output/capacities-debug.xlsx"
GEO_LOOKUP_JSON = "storage/output/geo_lookup.json"

GROUPED_CAPACITIES = "storage/output/grouped-capacities.xlsx"
GROUPED_FACTORIES = "storage/output/grouped-factories.xlsx"
GROUPED_INVESTMENTS = "storage/output/grouped-investments.xlsx"
ZEV_PRODUCTION = "storage/input/zev_og_clean.xlsx"

GRPD_PROJECTS = "./storage/output/all_projects.xlsx"
GRPD_PROJECTS_FILTER = "storage/output/filtered_projects.xlsx"
PRODUCT_CLASSIFICATION = "storage/input/product_classification.xlsx"
FACILITIES = "storage/output/facilities.xlsx"
CAPACITIES_PLOT = "storage/output/capacities_plot.xlsx"


grouped_facilities_cols = [
    "inst_canon", "inst_type", "owner_label", "iso2", "factory", "admin_group_key", 
    "product", "product_lv1", "product_lv2", "factory_status", "date", 
    "project_id", "project_key_str", "cluster_id", 
    "lat", "lon", "city_key", "adm1", "adm1-og", "adm2", "adm3", "adm4",
    "article_id"
]

grouped_capacities_cols = [
    "inst_canon", "inst_type", "owner_label", "iso2", "factory", "admin_group_key", 
    "product", "product_lv1", "product_lv2", "factory_status", "date",
    "capacity", "capacity_normalized", "capacity_metric_normalized", "phase", "status", 
    "project_id", "project_key_str", "cluster_id",
    "investment", "investment_status", "investment_phase", 
    "lat", "lon", "city_key", "adm1", "adm1-og", "adm2", "adm3", "adm4",
    "article_id", "investment_id"
]

grouped_investments_cols = [
    "inst_canon", "inst_type", "owner_label", "iso2", "factory", "admin_group_key", 
    "product", "product_lv1", "product_lv2", "factory_status", "date",
    "investment", "phase", "status", 
    "project_id", "project_key_str", "cluster_id", 
    "lat", "lon", "city_key", "adm1", "adm1-og", "adm2", "adm3", "adm4",
    "article_id", "investment_id"
]

GROUP_SPEC = [
        # (input_excel, output_excel, output_cols)
        (FACTORY_TECH_CLEAN_CAPACITIES, GROUPED_CAPACITIES, grouped_capacities_cols),
        (FACTORY_REGISTRY,  GROUPED_FACTORIES, grouped_facilities_cols),
        (INVESTMENT_FUNDS, GROUPED_INVESTMENTS, grouped_investments_cols)
    ]