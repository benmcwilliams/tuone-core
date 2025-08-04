# config.py

# Mongo query to filter articles to process (must have nodes & relationships)
# optional filter for meta.category.
ARTICLE_QUERY = {
    "nodes": {"$exists": True},
    "relationships": {"$exists": True},
    "meta.category": "electrive"
}

ARTICLE_PROJECTION = {
    "_id": 1,
    "nodes": 1,
    "relationships": 1
}

ALL_NODES = "storage/output/all_nodes.xlsx"
ALL_RELS = "storage/output/all_rels.xlsx"
FACTORY_TECH = "storage/output/factory-technological.xlsx"
GRPD_PROJECTS = "./storage/output/all_projects.xlsx"
GRPD_PROJECTS_FILTER = "storage/output/filtered_projects.xlsx"
PRODUCT_CLASSIFICATION = "storage/input/product_classification.xlsx"
FACILITIES = "storage/output/facilities.xlsx"