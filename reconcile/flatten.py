import sys; sys.path.append("..")  # allow access to parent folder modules
import logging
import pandas as pd
from reconcile.src.flatten_helpers import flatten_dict
from src.config import ARTICLE_QUERY, ARTICLE_PROJECTION, ALL_NODES, ALL_RELS
from mongo_client import articles_collection

# === OVERVIEW ===
# outputs flat (pandas) data for all nodes and relationships contained in the monogoDB collection
# each node or relationship is tagged to track which article it came from 

def run_flatten_articles():

    # 1.1: Query MongoDB for documents that have both 'nodes' and 'relationships' fields
    articles_to_process = list(
        articles_collection.find(
            ARTICLE_QUERY,
            ARTICLE_PROJECTION
        ).sort("_id", 1)
    )

    # 1.2: Initialize lists to collect all nodes and relationships
    all_nodes = []
    all_rels = []

    # 1.3: Loop through each document to flatten node and relationship data
    for doc in articles_to_process:
        article_id = str(doc.get("_id"))

        # 1.4: Process nodes - flatten structure and add article ID and label
        df_nodes = pd.DataFrame(doc.get("nodes", []))
        for _, row in df_nodes.iterrows():
            node_id = row.get("id")
            label = row.get("type", "Entity")

            if not node_id or not label:
                continue
            raw_props = {k: v for k, v in row.items() if k not in ["id", "type"]}
            flat_props = flatten_dict(raw_props)    # dictionary which outputs our location_city and location_country values
            flat_props.update({
                "article_id": article_id,
                "id": node_id,
                "label": label
            })
            all_nodes.append(flat_props)

        # 1.5: Process relationships - flatten and record key fields
        df_rels = pd.DataFrame(doc.get("relationships", []))
        for _, row in df_rels.iterrows():
            source = row.get("source")
            target = row.get("target")
            rel_type = row.get("type", "RELATED_TO")      # placeholder RELATED_TO in case of model non-conformity
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

    # 1.6: Convert all collected nodes and relationships into DataFrames
    df_all_nodes = pd.DataFrame(all_nodes)
    df_all_rels = pd.DataFrame(all_rels)
    print("Loaded to DataFrames: nodes =", len(df_all_nodes), "| relationships =", len(df_all_rels))

    # 1.7: Create unique IDs by combining article_id and node id
    df_all_nodes["unique_id"] = df_all_nodes["article_id"] + "_" + df_all_nodes["id"]

    # 1.8: Build lookup dictionaries to resolve IDs and types
    id_to_unique = df_all_nodes.set_index(['article_id', 'id'])['unique_id'].to_dict()
    id_to_label = df_all_nodes.set_index(['article_id', 'id'])['label'].to_dict()

    # 1.9: Define helper functions to map relationships to enriched labels and unique IDs
    def get_unique_id(row, which):
        return id_to_unique.get((row['article_id'], row[which]))

    def get_label(row, which):
        return id_to_label.get((row['article_id'], row[which]))

    # 1.10: Apply mapping to source and target fields in relationships
    df_all_rels['source_label'] = df_all_rels.apply(lambda row: get_label(row, 'source'), axis=1)
    df_all_rels['target_label'] = df_all_rels.apply(lambda row: get_label(row, 'target'), axis=1)
    df_all_rels['source'] = df_all_rels.apply(lambda row: get_unique_id(row, 'source'), axis=1)
    df_all_rels['target'] = df_all_rels.apply(lambda row: get_unique_id(row, 'target'), axis=1)

    # 1.12: Save raw flattened node and relationship data to Excel
    df_all_nodes.to_excel(ALL_NODES, 
                            index=False)
    df_all_rels.to_excel(ALL_RELS,
                                index=False)
    
    logging.info(f"-- tracking {len(df_all_nodes)} nodes")
    logging.info(f"-- tracking {len(df_all_rels)} relationships")
    logging.info(f"💾 Saved nodes to {ALL_NODES}")
    logging.info(f"💾 Saved relationships to {ALL_RELS}")

