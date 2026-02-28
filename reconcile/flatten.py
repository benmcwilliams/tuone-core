import sys; sys.path.append("..")  # allow access to parent folder modules
import logging
import pandas as pd
from reconcile.src.flatten_helpers import flatten_dict
from src.config import ARTICLE_QUERY, ARTICLE_PROJECTION, ALL_NODES, ALL_RELS
from mongo_client import articles_collection

# === OVERVIEW ===
# outputs flat (pandas) data for all nodes and relationships contained in the monogoDB collection
# each node or relationship is tagged to track which article it came from 

def run_flatten_articles(save: bool = False, debug_article_id: str | None = None, verbose: bool = False):

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
        for node in doc.get("nodes", []):
            node_id = node.get("id")
            label = node.get("type", "Entity")

            if not node_id or not label:
                continue
            raw_props = {k: v for k, v in node.items() if k not in ["id", "type"]}
            flat_props = flatten_dict(raw_props)    # dictionary which outputs our location_city and location_country values
            flat_props.update({
                "article_id": article_id,
                "id": node_id,
                "label": label
            })
            all_nodes.append(flat_props)

        # 1.5: Process relationships - flatten and record key fields
        for rel in doc.get("relationships", []):
            source = rel.get("source")
            target = rel.get("target")
            rel_type = rel.get("type", "RELATED_TO")      # placeholder RELATED_TO in case of model non-conformity
            group = rel.get("group", "unspecified")
            if not source or not target:
                continue
            raw_props = {k: v for k, v in rel.items() if k not in ["source", "target", "type", "group"]}
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
    if verbose:
        print("Loaded to DataFrames: nodes =", len(df_all_nodes), "| relationships =", len(df_all_rels))

    # 1.7: Create unique IDs by combining article_id and node id
    df_all_nodes["unique_id"] = df_all_nodes["article_id"] + "_" + df_all_nodes["id"]

    # 1.8–1.10: Resolve source/target labels and unique IDs via two left merges (vectorized)
    node_lookup = df_all_nodes[["article_id", "id", "unique_id", "label"]].copy()

    # First merge: source node → source_label, source_unique_id
    src_lookup = node_lookup.rename(columns={"id": "src_node_id", "unique_id": "source_unique_id", "label": "source_label"})
    df_all_rels = df_all_rels.merge(
        src_lookup,
        left_on=["article_id", "source"],
        right_on=["article_id", "src_node_id"],
        how="left",
    ).drop(columns=["src_node_id"], errors="ignore")

    # Second merge: target node → target_label, target_unique_id
    tgt_lookup = node_lookup.rename(columns={"id": "tgt_node_id", "unique_id": "target_unique_id", "label": "target_label"})
    df_all_rels = df_all_rels.merge(
        tgt_lookup,
        left_on=["article_id", "target"],
        right_on=["article_id", "tgt_node_id"],
        how="left",
    ).drop(columns=["tgt_node_id"], errors="ignore")

    # Overwrite source/target with unique IDs and drop temporary columns
    df_all_rels["source"] = df_all_rels["source_unique_id"]
    df_all_rels["target"] = df_all_rels["target_unique_id"]
    df_all_rels = df_all_rels.drop(columns=["source_unique_id", "target_unique_id"], errors="ignore")

    # Debug: log factory nodes for one article (non-invasive when debug_article_id is None)
    if debug_article_id and "article_id" in df_all_nodes.columns:
        fac = df_all_nodes[
            (df_all_nodes["article_id"] == debug_article_id)
            & (df_all_nodes["label"].str.lower().str.contains("factory", na=False))
        ]
        if fac.empty:
            logging.info(
                "[DEBUG flatten] article %s: no factory rows",
                debug_article_id,
            )
        else:
            has_loc_city = "location_city" in fac.columns and fac["location_city"].notna().any()
            has_loc_country = "location_country" in fac.columns and fac["location_country"].notna().any()
            logging.info(
                "[DEBUG flatten] article %s: factory rows=%d, has location_city=%s, location_country=%s",
                debug_article_id,
                len(fac),
                has_loc_city,
                has_loc_country,
            )

    # 1.12: Save raw flattened node and relationship data to Excel
    if save:
        df_all_nodes.to_excel(ALL_NODES, 
                                index=False)
        df_all_rels.to_excel(ALL_RELS,
                                    index=False)
        
        logging.info(f"💾 Saved nodes to {ALL_NODES}")
        logging.info(f"💾 Saved relationships to {ALL_RELS}")

    return df_all_nodes, df_all_rels

