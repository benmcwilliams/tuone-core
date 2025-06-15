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
from to_pandas_helpers import flatten_dict
from mongo_client import mongo_client, articles_collection

# === Query articles from MongoDB ===
articles_to_process = list(
    articles_collection.find(
        {
            "nodes": {"$exists": True},         # nodes field must exist
            "relationships": {"$exists": True}  # relationship field must exist
        },
        {
            "_id": 1, "nodes": 1, "relationships": 1 # return the mongodb _id, nodes and relationships
        }
    ).sort("_id", 1)
)

# === Process nodes and relationships ===
all_nodes = []
all_rels = []

for doc in articles_to_process:

    article_id = str(doc.get("_id"))

    # === Nodes ===
    df_nodes = pd.DataFrame(doc.get("nodes", []))
    for _, row in df_nodes.iterrows():
        node_id = row.get("id")
        label = row.get("type", "Entity")
        if not node_id or not label:
            continue
        raw_props = {k: v for k, v in row.items() if k not in ["id", "type"]}
        flat_props = flatten_dict(raw_props)
        flat_props.update({
            "article_id": article_id,
            "id": node_id,
            "label": label
        })
        all_nodes.append(flat_props)

    # === Relationships ===
    df_rels = pd.DataFrame(doc.get("relationships", []))
    for _, row in df_rels.iterrows():
        source = row.get("source")
        target = row.get("target")
        rel_type = row.get("type", "RELATED_TO")
        group = row.get("group", "unspecified")
        if not source or not target:
            continue
        raw_props = {k: v for k, v in row.items() if k not in ["source", "target", "type", "group"]}
        flat_props = flatten_dict(raw_props)
        flat_props.update({
            "article_id": article_id,
            "source": source,
            "target": target,
            "type": rel_type,
            "group": group
        })
        all_rels.append(flat_props)

# === Convert to DataFrames ===
df_all_nodes = pd.DataFrame(all_nodes)
df_all_rels = pd.DataFrame(all_rels)

print("Loaded to DataFrames: nodes =", len(df_all_nodes), "| relationships =", len(df_all_rels))

# === Create unique_id for each node ===
df_all_nodes["unique_id"] = df_all_nodes["article_id"] + "_" + df_all_nodes["id"]

# === Create lookup dictionaries ===
id_to_unique = df_all_nodes.set_index(['article_id', 'id'])['unique_id'].to_dict()
id_to_label = df_all_nodes.set_index(['article_id', 'id'])['label'].to_dict()

# === Map source and target to unique_id and label ===
def get_unique_id(row, which):
    return id_to_unique.get((row['article_id'], row[which]))

def get_label(row, which):
    return id_to_label.get((row['article_id'], row[which]))

df_all_rels['source_label'] = df_all_rels.apply(lambda row: get_label(row, 'source'), axis=1)
df_all_rels['target_label'] = df_all_rels.apply(lambda row: get_label(row, 'target'), axis=1)
df_all_rels['source'] = df_all_rels.apply(lambda row: get_unique_id(row, 'source'), axis=1)
df_all_rels['target'] = df_all_rels.apply(lambda row: get_unique_id(row, 'target'), axis=1)

df_all_nodes.to_excel("output/all_nodes.xlsx")
df_all_rels.to_excel("output/all_rels.xlsx")

# === Helper Functions ===

def safe_lookup_list(ids, lookup, key):
    if not isinstance(ids, list):
        return []
    result = [lookup.get(i, {}).get(key, None) for i in ids]
    while len(result) < len(ids):
        result.append(None)
    return result[:len(ids)]

def build_reconciliation_lookup(log):
    df_log = pd.DataFrame(log)
    df_log["article_id"] = df_log["original_unique_id"].str.extract(r"(^[^_]+)")
    product_ids = df_log[df_log["entity_type"] == "product"].groupby("new_unique_id")["article_id"].apply(set).to_dict()
    company_ids = df_log[df_log["entity_type"] == "company"].groupby("new_unique_id")["article_id"].apply(set).to_dict()
    jv_ids = df_log[df_log["entity_type"] == "joint_venture"].groupby("new_unique_id")["article_id"].apply(set).to_dict()
    investment_ids = df_log[df_log["entity_type"] == "investment"].groupby("new_unique_id")["article_id"].apply(set).to_dict()
    capacity_ids = df_log[df_log["entity_type"] == "capacity"].groupby("new_unique_id")["article_id"].apply(set).to_dict()

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
    #very small number of exact duplicates which we remove - consider dropping this
    return (
        df_nodes.drop_duplicates(subset="unique_id"),
        df_rels.drop_duplicates(subset=["source", "target", "type"])
    )

def extract_node_subsets(df_nodes):
    return {
        "joint_ventures": df_nodes[df_nodes["label"].str.lower() == "joint_venture"],
        "factories": df_nodes[df_nodes["label"].str.lower().str.contains("factory", na=False)].copy(),
        "capacities": df_nodes[df_nodes["label"].str.lower() == "capacity"],
        "products": df_nodes[df_nodes["label"].str.lower() == "product"],
        "companies": df_nodes[df_nodes["label"].str.lower() == "company"],
        "investment": df_nodes[df_nodes["label"].str.lower() == "investment"]
    }

def extract_relationship_subsets(df_rels):
    return {
        "owns": df_rels[df_rels["type"].str.lower() == "owns"],
        "at": df_rels[df_rels["type"].str.lower() == "at"],
        "produced_at": df_rels[df_rels["type"].str.lower() == "produced_at"],
        "funds": df_rels[df_rels["type"].str.lower() == "funds"]
    }

def group_linked_nodes(rel_df, source_nodes, source_col, target_col, entity_label_prefix):
    rel_df = rel_df.copy()
    df = rel_df.rename(columns={"source": source_col, "target": target_col})
    df = df.merge(
        source_nodes[["unique_id", "name"]].rename(columns={
            "unique_id": f"{entity_label_prefix}_unique_id",
            "name": f"{entity_label_prefix}_name",
        }),
        left_on=source_col, right_on=f"{entity_label_prefix}_unique_id", how="left"
    )
    grouped = df.groupby(target_col).agg({
        f"{entity_label_prefix}_unique_id": lambda x: list(x.dropna().unique()),
        f"{entity_label_prefix}_name": lambda x: list(x.dropna().unique()),
    }).reset_index().rename(columns={target_col: "factory_unique_id"})
    return grouped

def run_factory_centric_enrichment(df_all_nodes, df_all_rels):
    # capacity_article_ids, product_article_ids, company_article_ids, joint_venture_article_ids, investment_article_ids = build_reconciliation_lookup(main_reconciliation_log)

    df_all_nodes, df_all_rels = deduplicate_nodes_and_rels(df_all_nodes, df_all_rels)

    nodes = extract_node_subsets(df_all_nodes)
    rels = extract_relationship_subsets(df_all_rels)

    # Extract city and country from already flattened factory nodes
    df_factory_locations = nodes["factories"][["name", "unique_id", "location_city", "location_country"]].rename(
        columns={
            "unique_id": "factory_unique_id",
            "location_city": "factory_city",
            "location_country": "factory_country",
            "name":"factory_name",
            "article_id": "article_id"
        }
    )

    df_owns_comp = group_linked_nodes(rels["owns"], nodes["companies"], "source", "target", "owner_company")
    df_owns_jv = group_linked_nodes(rels["owns"], nodes["joint_ventures"], "source", "target", "owner_jv")
    df_funds = group_linked_nodes(rels["funds"], nodes["investment"], "source", "target", "investment")
    df_products = group_linked_nodes(rels["produced_at"], nodes["products"], "source", "target", "product")
    df_capacities = group_linked_nodes(rels["at"], nodes["capacities"], "source", "target", "capacity")

    df_master = reduce(lambda left, right: pd.merge(left, right, on="factory_unique_id", how="outer"), [
        df_owns_comp, df_owns_jv, df_funds, df_products, df_capacities
    ])
    # Merge city and country info
    df_master = df_master.merge(df_factory_locations, on="factory_unique_id", how="left")

    inv_lookup = nodes["investment"].set_index("unique_id")[["name", "status", "amount", "phase"]].to_dict("index")
    cap_lookup = nodes["capacities"].set_index("unique_id")[["name", "status", "amount", "phase"]].to_dict("index")

    df_master["investment_name"] = df_master["investment_unique_id"].apply(lambda uids: safe_lookup_list(uids, inv_lookup, "name"))
    df_master["investment_status"] = df_master["investment_unique_id"].apply(lambda uids: safe_lookup_list(uids, inv_lookup, "status"))
    df_master["investment_amount"] = df_master["investment_unique_id"].apply(lambda uids: safe_lookup_list(uids, inv_lookup, "amount"))
    df_master["investment_phase"] = df_master["investment_unique_id"].apply(lambda uids: safe_lookup_list(uids, inv_lookup, "phase"))

    df_master["capacity_name"] = df_master["capacity_unique_id"].apply(lambda ids: safe_lookup_list(ids, cap_lookup, "name"))
    df_master["capacity_status"] = df_master["capacity_unique_id"].apply(lambda ids: safe_lookup_list(ids, cap_lookup, "status"))
    df_master["capacity_amount"] = df_master["capacity_unique_id"].apply(lambda ids: safe_lookup_list(ids, cap_lookup, "amount"))
    df_master["capacity_phase"] = df_master["capacity_unique_id"].apply(lambda ids: safe_lookup_list(ids, cap_lookup, "phase"))

    df_master_final = df_master[[
        "factory_name", "factory_country", "factory_city",
        "owner_company_name", 
        "owner_jv_name", 
        "product_name", 
        "capacity_name", "capacity_status",  "capacity_phase", "capacity_amount",
        "investment_name", "investment_status", "investment_phase", "investment_amount", 
    ]]

    df_factories_pivot = df_master.explode(["factory_unique_id"])
    df_owner_companies_pivot = df_master.explode("owner_company_name")
    df_owner_jvs_pivot = df_master.explode("owner_jv_name")
    df_products_pivot = df_master.explode(["product_name"])
    df_capacities_pivot = df_master.explode(["capacity_name", "capacity_status", "capacity_amount", "capacity_phase"])
    df_investments_pivot = df_master.explode(["investment_name", "investment_status", "investment_amount", "investment_phase"])

    with pd.ExcelWriter("output/reconciliation_outputs_factory.xlsx", engine="openpyxl") as writer:
        df_master.to_excel(writer, sheet_name="factory", index=False)
        df_master_final.to_excel(writer, sheet_name="summary_view_factory", index=False)
        df_factories_pivot.to_excel(writer, sheet_name="pivot_factories", index=False)
        df_owner_companies_pivot.to_excel(writer, sheet_name="pivot_owner_companies", index=False)
        df_owner_jvs_pivot.to_excel(writer, sheet_name="pivot_owner_jvs", index=False)
        df_products_pivot.to_excel(writer, sheet_name="pivot_products", index=False)
        df_capacities_pivot.to_excel(writer, sheet_name="pivot_capacities", index=False)
        df_investments_pivot.to_excel(writer, sheet_name="pivot_investments", index=False)

    print("\u2705 Saved factory-centric outputs to reconciliation_outputs_factory.xlsx")

# run
run_factory_centric_enrichment(df_all_nodes, df_all_rels)