import sys; sys.path.append("..")  # allow access to parent folder modules
import logging
import pandas as pd
from collections import Counter
from reconcile.src.flatten_helpers import flatten_dict
from src.config import ARTICLE_QUERY, ARTICLE_PROJECTION, ALL_NODES, ALL_RELS
from mongo_client import articles_collection
from src.debug_helpers import get_debug_tracker

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

    # Debug: write to per-article log file only (no main console)
    tracker = get_debug_tracker()
    if debug_article_id and tracker is not None and tracker.article_id == debug_article_id:
        tracker.section("Flatten: article summary")
        sub_nodes = df_all_nodes[df_all_nodes["article_id"] == debug_article_id]
        sub_rels = df_all_rels[df_all_rels["article_id"] == debug_article_id]
        if sub_nodes.empty and sub_rels.empty:
            tracker.warn(
                "Article has 0 nodes and 0 relationships in flattened data. "
                "This usually means the document was not returned by the MongoDB query: "
                "check that meta.category is in ARTICLE_QUERY in reconcile/src/config.py (e.g. add \"enrichment\" if this is an enrichment article)."
            )
        node_types = Counter(sub_nodes["label"].astype(str).str.lower()) if "label" in sub_nodes.columns else {}
        rel_types = Counter(sub_rels["type"].astype(str).str.lower()) if "type" in sub_rels.columns else {}
        tracker.info("Node counts by type: %s", dict(node_types))
        tracker.info("Relationship counts by type: %s", dict(rel_types))
        if not sub_rels.empty and "source_label" in sub_rels.columns and "target_label" in sub_rels.columns:
            missing_src = sub_rels["source_label"].isna().sum()
            missing_tgt = sub_rels["target_label"].isna().sum()
            if missing_src or missing_tgt:
                tracker.warn("Unresolved relation endpoints: source_label missing=%d, target_label missing=%d", missing_src, missing_tgt)
        fac = sub_nodes[sub_nodes["label"].astype(str).str.lower().str.contains("factory", na=False)]
        if fac.empty:
            tracker.info("No factory nodes in this article.")
        else:
            has_loc_city = "location_city" in fac.columns and fac["location_city"].notna().any()
            has_loc_country = "location_country" in fac.columns and fac["location_country"].notna().any()
            tracker.info("Factory rows=%d, has location_city=%s, location_country=%s", len(fac), has_loc_city, has_loc_country)

    # 1.12: Save raw flattened node and relationship data to Excel
    if save:
        df_all_nodes.to_excel(ALL_NODES, 
                                index=False)
        df_all_rels.to_excel(ALL_RELS,
                                    index=False)
        
        logging.info(f"💾 Saved nodes to {ALL_NODES}")
        logging.info(f"💾 Saved relationships to {ALL_RELS}")

    return df_all_nodes, df_all_rels

