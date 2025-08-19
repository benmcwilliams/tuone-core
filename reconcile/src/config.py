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
FACTORY_TECH = "storage/output/factory-technological.xlsx"
FACTORY_TECH_CLEAN_CAPACITIES = "storage/output/factory-technological-clean-capacities.xlsx"
CAPACITIES_DEBUG = "storage/output/capacities-debug.xlsx"
GEO_LOOKUP_JSON = "storage/output/geo_lookup.json"

GRPD_PROJECTS = "./storage/output/all_projects.xlsx"
GRPD_PROJECTS_FILTER = "storage/output/filtered_projects.xlsx"
PRODUCT_CLASSIFICATION = "storage/input/product_classification.xlsx"
FACILITIES = "storage/output/facilities.xlsx"
CAPACITIES_PLOT = "storage/output/capacities_plot.xlsx"