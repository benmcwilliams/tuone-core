# config.py

# Mongo query to filter articles to process (must have nodes & relationships)
# optional filter for meta.category.
ARTICLE_QUERY = {
    "nodes": {"$exists": True},
    "relationships": {"$exists": True},
    "meta.category": {"$in": ["user", "user_text", "electrive", "justauto", "pvmagazine", "pvtech", "world_energy"]}
}

ARTICLE_PROJECTION = {
    "_id": 1,
    "nodes": 1,
    "relationships": 1
}

# builder files
ALL_NODES = "storage/output/all_nodes.xlsx"
ALL_RELS = "storage/output/all_rels.xlsx"
GEO_LOOKUP_JSON = "storage/output/geo_lookup.json"

# raw views
FACTORY_REGISTRY = "storage/output/factory_registry.xlsx"
FACTORY_TECH = "storage/output/factory-technological.xlsx"
COMPANY_JV = "storage/output/company-joint-venture.xlsx"
INVESTMENT_FUNDS = "storage/output/investment-funds-factory.xlsx"

# cleaning capacities and investments
FACTORY_TECH_CLEAN_CAPACITIES = "storage/output/factory-technological-clean-capacities.xlsx"
FACTORY_TECH_CLEAN_CAPACITIES_INVESTMENTS = "storage/output/factory-technological-clean-capacities-investments.xlsx"
CLEAN_INVESTMENT_FUNDS = "storage/output/clean-investment-funds-factory.xlsx"
CAPACITIES_DEBUG = "storage/output/capacities-debug.xlsx"

# grouping
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
    "capacity", "capacity_normalized", "capacity_metric_normalized", "phase", "status", "additional", "capacity_id", 
    "project_id", "project_key_str", "cluster_id",
    "investment", "amount_EUR", "investment_status", "investment_phase", "is_total", 
    "lat", "lon", "city_key", "adm1", "adm1-og", "adm2", "adm3", "adm4",
    "article_id", "investment_id"
]

grouped_investments_cols = [
    "inst_canon", "inst_type", "owner_label", "iso2", "factory", "admin_group_key", 
    "product", "product_lv1", "product_lv2", "factory_status", "date",
    "investment", "amount_EUR", "phase", "status", "is_total",
    "project_id", "project_key_str", "cluster_id", 
    "lat", "lon", "city_key", "adm1", "adm1-og", "adm2", "adm3", "adm4",
    "article_id", "investment_id"
]

GROUP_SPEC = [
        # (input_excel, output_excel, output_cols)
        (FACTORY_TECH_CLEAN_CAPACITIES_INVESTMENTS, GROUPED_CAPACITIES, grouped_capacities_cols),
        (FACTORY_REGISTRY,  GROUPED_FACTORIES, grouped_facilities_cols),
        (CLEAN_INVESTMENT_FUNDS, GROUPED_INVESTMENTS, grouped_investments_cols)
    ]