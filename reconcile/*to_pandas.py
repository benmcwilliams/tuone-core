# 1.1: Import necessary libraries and modules
import sys; sys.path.append("..")  # allow access to parent folder modules
from rapidfuzz import fuzz
import pandas as pd
import os
import re
from datetime import datetime
from pymongo import MongoClient
from itertools import combinations
from collections import defaultdict
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from functools import reduce
from reconcile.src.flatten_helpers import flatten_dict
from mongo_client import mongo_client, articles_collection

# === OVERVIEW ===
# This script extracts and processes data from a MongoDB collection where each article includes nodes (e.g., companies, factories, investments) 
# and relationships (e.g., owns, funds, produced_at). Each node is given a unique ID by combining its article ID and internal ID to ensure global uniqueness.
# Relationships reference node IDs, so these are translated to the new unique node IDs. Each source and target in a relationship is also enriched
# with the type of node it refers to (e.g., company, factory), using the original node metadata. This makes it easier to group and interpret relationships later.
# 
# The pipeline focuses on factories: it identifies which companies or joint ventures own them, which investments fund them, 
# what products are made there, and what capacities are installed. This is done by grouping relationship data by factory ID and enriching it 
# using metadata from the original nodes (such as name, phase, amount, status).
# 
# The result is a set of clean Excel files where each factory has its ecosystem (direct links) of owners, products, investments, and capacities clearly organised
# into summary and pivoted views for easy exploration.

# 1.2: Query MongoDB for documents that have both 'nodes' and 'relationships' fields
articles_to_process = list(
    articles_collection.find(
        {
            "nodes": {"$exists": True},
            "relationships": {"$exists": True},
            "llm_processed.run_id": "v1"
        },
        {
            "_id": 1, "nodes": 1, "relationships": 1
        }
    ).sort("_id", 1)
)

# # 1.3: Initialize lists to collect all nodes and relationships
# all_nodes = []
# all_rels = []

# # 1.4: Loop through each document to flatten node and relationship data
# for doc in articles_to_process:
#     article_id = str(doc.get("_id"))

#     # 1.5: Process nodes - flatten structure and add article ID and label
#     df_nodes = pd.DataFrame(doc.get("nodes", []))
#     for _, row in df_nodes.iterrows():
#         node_id = row.get("id")
#         label = row.get("type", "Entity")

#         if not node_id or not label:
#             continue
#         raw_props = {k: v for k, v in row.items() if k not in ["id", "type"]}
#         flat_props = flatten_dict(raw_props)    # dictionary which outputs our location_city and location_country values
#         flat_props.update({
#             "article_id": article_id,
#             "id": node_id,
#             "label": label
#         })
#         all_nodes.append(flat_props)

#     # 1.6: Process relationships - flatten and record key fields
#     df_rels = pd.DataFrame(doc.get("relationships", []))
#     for _, row in df_rels.iterrows():
#         source = row.get("source")
#         target = row.get("target")
#         rel_type = row.get("type", "RELATED_TO")      # placeholder RELATED_TO in case of model non-conformity
#         group = row.get("group", "unspecified")
#         if not source or not target:
#             continue
#         raw_props = {k: v for k, v in row.items() if k not in ["source", "target", "type", "group"]}
#         flat_props = flatten_dict(raw_props)
#         flat_props.update({
#             "article_id": article_id,
#             "source": source,
#             "target": target,
#             "type": rel_type,
#             "group": group
#         })
#         all_rels.append(flat_props)

# # 1.7: Convert all collected nodes and relationships into DataFrames
# df_all_nodes = pd.DataFrame(all_nodes)
# df_all_rels = pd.DataFrame(all_rels)
# print("Loaded to DataFrames: nodes =", len(df_all_nodes), "| relationships =", len(df_all_rels))

# # 1.8: Create unique IDs by combining article_id and node id
# df_all_nodes["unique_id"] = df_all_nodes["article_id"] + "_" + df_all_nodes["id"]

# # 1.9: Build lookup dictionaries to resolve IDs and types
# id_to_unique = df_all_nodes.set_index(['article_id', 'id'])['unique_id'].to_dict()
# id_to_label = df_all_nodes.set_index(['article_id', 'id'])['label'].to_dict()

# # 1.10: Define helper functions to map relationships to enriched labels and unique IDs
# def get_unique_id(row, which):
#     return id_to_unique.get((row['article_id'], row[which]))

# def get_label(row, which):
#     return id_to_label.get((row['article_id'], row[which]))

# # 1.11: Apply mapping to source and target fields in relationships
# df_all_rels['source_label'] = df_all_rels.apply(lambda row: get_label(row, 'source'), axis=1)
# df_all_rels['target_label'] = df_all_rels.apply(lambda row: get_label(row, 'target'), axis=1)
# df_all_rels['source'] = df_all_rels.apply(lambda row: get_unique_id(row, 'source'), axis=1)
# df_all_rels['target'] = df_all_rels.apply(lambda row: get_unique_id(row, 'target'), axis=1)

# # 1.12: Save raw flattened node and relationship data to Excel
# df_all_nodes.to_excel("storage/output/all_nodes.xlsx")
# df_all_rels.to_excel("storage/output/all_rels.xlsx")

# 2. Start enrichment: main function is defined at the end
# Commenting will continue through function and helper definitions

def safe_lookup_list(ids, lookup, key):
    # 4.1: For a list of IDs, retrieve values from a lookup dict using a key
    # If any ID is missing or not found, fill with None to keep alignment
    if not isinstance(ids, list):
        return []
    result = [lookup.get(i, {}).get(key, None) for i in ids]
    while len(result) < len(ids):
        result.append(None)
    return result[:len(ids)]

def build_reconciliation_lookup(log):
    # [UNUSED IN CURRENT FLOW] Generates lookup dictionaries for each entity type from a reconciliation log
    df_log = pd.DataFrame(log)
    df_log["article_id"] = df_log["original_unique_id"].str.extract(r"(^[^_]+)")
    product_ids = df_log[df_log["entity_type"] == "product"].groupby("new_unique_id")["article_id"].apply(set).to_dict()
    company_ids = df_log[df_log["entity_type"] == "company"].groupby("new_unique_id")["article_id"].apply(set).to_dict()
    jv_ids = df_log[df_log["entity_type"] == "joint_venture"].groupby("new_unique_id")["article_id"].apply(set).to_dict()
    investment_ids = df_log[df_log["entity_type"] == "investment"].groupby("new_unique_id")["article_id"].apply(set).to_dict()
    capacity_ids = df_log[df_log["entity_type"] == "capacity"].groupby("new_unique_id")["article_id"].apply(set).to_dict()

    # Fill in fallbacks for unmatched entries
    for uid in df_log["new_unique_id"]:
        fallback = {uid.split("_")[0]}
        if uid.startswith("product_"):
            product_ids.setdefault(uid, fallback)
        elif uid.startswith("company_"):
            company_ids.setdefault(uid, fallback)
        elif uid.startswith("investment_"):
            investment_ids.setdefault(uid, fallback)
        elif uid.startswith("capacity_"):
            capacity_ids.setdefault(uid, fallback)
        elif uid.startswith("joint_venture_"):
            jv_ids.setdefault(uid, fallback)

    return df_log, capacity_ids, product_ids, company_ids, jv_ids, investment_ids

def deduplicate_nodes_and_rels(df_nodes, df_rels):
    # 2.1: Remove duplicate rows by unique_id (nodes) and source-target-type triplet (rels)
    return (
        df_nodes.drop_duplicates(subset="unique_id"),
        df_rels.drop_duplicates(subset=["source", "target", "type"])
    )

def extract_node_subsets(df_nodes):
    # 2.2: Split the df_all_nodes DataFrame into subsets by label for different entity types
    return {
        "joint_venture": df_nodes[df_nodes["label"].str.lower() == "joint_venture"],
        "factory": df_nodes[df_nodes["label"].str.lower().str.contains("factory", na=False)].copy(),
        "capacity": df_nodes[df_nodes["label"].str.lower() == "capacity"],
        "product": df_nodes[df_nodes["label"].str.lower() == "product"],
        "company": df_nodes[df_nodes["label"].str.lower() == "company"],
        "investment": df_nodes[df_nodes["label"].str.lower() == "investment"]
    }

def extract_relationship_subsets(df_rels):
    # 2.3: Split df_all_rels into subsets by relationship type (owns, at, etc.)
    return {
        "owns": df_rels[df_rels["type"].str.lower() == "owns"],
        "at": df_rels[df_rels["type"].str.lower() == "at"],
        "produced_at": df_rels[df_rels["type"].str.lower() == "produced_at"],
        "funds": df_rels[df_rels["type"].str.lower() == "funds"]
    }

def group_linked_nodes(rel_df, source_nodes, source_col, target_col, entity_label_prefix):
    # 3.X: Generic function to group relationships by target node (factory), collecting info from source nodes
    rel_df = rel_df.copy()
    df = rel_df.rename(columns={"source": source_col, "target": target_col})

    # Join with source node metadata to retrieve names
    df = df.merge(
        source_nodes[["unique_id", "name"]].rename(columns={
            "unique_id": f"{entity_label_prefix}_unique_id",
            "name": f"{entity_label_prefix}_name",
        }),
        left_on=source_col, right_on=f"{entity_label_prefix}_unique_id", how="left"
    )

    # Group by target (factory) and aggregate lists of source IDs and names
    grouped = df.groupby(target_col).agg({
        f"{entity_label_prefix}_unique_id": lambda x: list(x.dropna().unique()),
        f"{entity_label_prefix}_name": lambda x: list(x.dropna().unique()),
    }).reset_index().rename(columns={target_col: "factory_unique_id"})
    return grouped

df_all_nodes = pd.read_excel("storage/output/all_nodes.xlsx")
df_all_rels = pd.read_excel("storage/output/all_rels.xlsx")

# === Section 2.4–5.4: Full enrichment pipeline ===
def run_factory_centric_enrichment(df_all_nodes, df_all_rels):
    # Deduplicate raw data
    df_all_nodes, df_all_rels = deduplicate_nodes_and_rels(df_all_nodes, df_all_rels)

    # 2.2–2.3: Break nodes and relationships into subsets
    nodes = extract_node_subsets(df_all_nodes)
    rels = extract_relationship_subsets(df_all_rels)

    # 3.6: Extract factory metadata: name, city, country
    df_factory_locations = nodes["factory"][[
        "name", "unique_id", "location_city", "location_country"
    ]].rename(columns={
        "unique_id": "factory_unique_id",
        "location_city": "factory_city",
        "location_country": "factory_country",
        "name": "factory_name"
    })

    # 3.1–3.5: Group by relationships
    df_owns_comp = group_linked_nodes(rels["owns"], nodes["company"], "source", "target", "owner_company")
    df_owns_jv = group_linked_nodes(rels["owns"], nodes["joint_venture"], "source", "target", "owner_jv")
    df_funds = group_linked_nodes(rels["funds"], nodes["investment"], "source", "target", "investment")
    df_products = group_linked_nodes(rels["produced_at"], nodes["product"], "source", "target", "product")
    df_capacities = group_linked_nodes(rels["at"], nodes["capacity"], "source", "target", "capacity")

    # 3.7–3.8: Merge all grouped attributes into master factory table
    df_master = reduce(lambda left, right: pd.merge(left, right, on="factory_unique_id", how="outer"), [
        df_owns_comp, df_owns_jv, df_funds, df_products, df_capacities
    ])
    df_master = df_master.merge(df_factory_locations, on="factory_unique_id", how="left")

    # 4.1: Create enrichment lookup dictionaries
    inv_lookup = nodes["investment"].set_index("unique_id")[["name", "status", "amount", "phase"]].to_dict("index")
    cap_lookup = nodes["capacity"].set_index("unique_id")[["name", "status", "amount", "phase"]].to_dict("index")
    #prod_lookup = nodes["product"].set_index("unique_id")[["technology"]].to_dict("index")

    # 4.2: Enrich investments using lookup
    df_master["investment_name"] = df_master["investment_unique_id"].apply(lambda uids: safe_lookup_list(uids, inv_lookup, "name"))
    df_master["investment_status"] = df_master["investment_unique_id"].apply(lambda uids: safe_lookup_list(uids, inv_lookup, "status"))
    df_master["investment_amount"] = df_master["investment_unique_id"].apply(lambda uids: safe_lookup_list(uids, inv_lookup, "amount"))
    df_master["investment_phase"] = df_master["investment_unique_id"].apply(lambda uids: safe_lookup_list(uids, inv_lookup, "phase"))

    # 4.3: Enrich capacities using lookup
    df_master["capacity_name"] = df_master["capacity_unique_id"].apply(lambda ids: safe_lookup_list(ids, cap_lookup, "name"))
    df_master["capacity_status"] = df_master["capacity_unique_id"].apply(lambda ids: safe_lookup_list(ids, cap_lookup, "status"))
    df_master["capacity_amount"] = df_master["capacity_unique_id"].apply(lambda ids: safe_lookup_list(ids, cap_lookup, "amount"))
    df_master["capacity_phase"] = df_master["capacity_unique_id"].apply(lambda ids: safe_lookup_list(ids, cap_lookup, "phase"))

    # 5.1: Define summary output
    df_master_final = df_master[[
        "factory_name", "factory_country", "factory_city",
        "owner_company_name", 
        "owner_jv_name", 
        "product_name",
        "capacity_name", "capacity_status",  "capacity_phase", "capacity_amount",
        "investment_name", "investment_status", "investment_phase", "investment_amount", 
    ]]

    df_master_final[["owner_company_name","factory_country","factory_city","factory_name","product_name",
                     "capacity_amount","capacity_status","capacity_phase"]].to_excel("storage/output/capacities.xlsx")

    # 5.2: Pivot for views
    df_factories_pivot = df_master.explode(["factory_unique_id"])
    df_owner_companies_pivot = df_master.explode("owner_company_name")
    df_owner_jvs_pivot = df_master.explode("owner_jv_name")
    df_products_pivot = df_master.explode(["product_name"])
    df_capacities_pivot = df_master.explode(["capacity_name", "capacity_status", "capacity_amount", "capacity_phase"])
    df_investments_pivot = df_master.explode(["investment_name", "investment_status", "investment_amount", "investment_phase"])

    # 5.3: Save everything to Excel
    with pd.ExcelWriter("storage/output/reconciliation_outputs_factory.xlsx", engine="openpyxl") as writer:
        df_master.to_excel(writer, sheet_name="factory", index=False)
        df_master_final.to_excel(writer, sheet_name="summary_view_factory", index=False)
        df_factories_pivot.to_excel(writer, sheet_name="pivot_factories", index=False)
        df_owner_companies_pivot.to_excel(writer, sheet_name="pivot_owner_companies", index=False)
        df_owner_jvs_pivot.to_excel(writer, sheet_name="pivot_owner_jvs", index=False)
        df_products_pivot.to_excel(writer, sheet_name="pivot_products", index=False)
        df_capacities_pivot.to_excel(writer, sheet_name="pivot_capacities", index=False)
        df_investments_pivot.to_excel(writer, sheet_name="pivot_investments", index=False)

    # 5.4: Done
    print("\u2705 Saved factory-centric outputs to reconciliation_outputs_factory.xlsx")

#  Run the pipeline
run_factory_centric_enrichment(df_all_nodes, df_all_rels)
