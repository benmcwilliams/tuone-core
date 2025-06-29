import sys; sys.path.append("..")  # allow access to parent folder modules
import pandas as pd
from src.to_pandas_helpers import flatten_dict
from mongo_client import mongo_client, articles_collection

# === OVERVIEW ===
# the script outputs flat structured (pandas) table data for all nodes and relationships contained in the monogoDB collection
# each node or relationship is tagged to retain a track of which article it came from 

# 1.2: Query MongoDB for documents that have both 'nodes' and 'relationships' fields
articles_to_process = list(
    articles_collection.find(
        {
            "nodes": {"$exists": True},
            "relationships": {"$exists": True},
            "llm_processed.run_id": "v0"
        },
        {
            "_id": 1, "nodes": 1, "relationships": 1
        }
    ).sort("_id", 1)
    .limit(400)
)

# 1.3: Initialize lists to collect all nodes and relationships
all_nodes = []
all_rels = []

# 1.4: Loop through each document to flatten node and relationship data
for doc in articles_to_process:
    article_id = str(doc.get("_id"))

    # 1.5: Process nodes - flatten structure and add article ID and label
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

    # 1.6: Process relationships - flatten and record key fields
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

# 1.7: Convert all collected nodes and relationships into DataFrames
df_all_nodes = pd.DataFrame(all_nodes)
df_all_rels = pd.DataFrame(all_rels)
print("Loaded to DataFrames: nodes =", len(df_all_nodes), "| relationships =", len(df_all_rels))

# 1.8: Create unique IDs by combining article_id and node id
df_all_nodes["unique_id"] = df_all_nodes["article_id"] + "_" + df_all_nodes["id"]

# 1.9: Build lookup dictionaries to resolve IDs and types
id_to_unique = df_all_nodes.set_index(['article_id', 'id'])['unique_id'].to_dict()
id_to_label = df_all_nodes.set_index(['article_id', 'id'])['label'].to_dict()

# 1.10: Define helper functions to map relationships to enriched labels and unique IDs
def get_unique_id(row, which):
    return id_to_unique.get((row['article_id'], row[which]))

def get_label(row, which):
    return id_to_label.get((row['article_id'], row[which]))

# 1.11: Apply mapping to source and target fields in relationships
df_all_rels['source_label'] = df_all_rels.apply(lambda row: get_label(row, 'source'), axis=1)
df_all_rels['target_label'] = df_all_rels.apply(lambda row: get_label(row, 'target'), axis=1)
df_all_rels['source'] = df_all_rels.apply(lambda row: get_unique_id(row, 'source'), axis=1)
df_all_rels['target'] = df_all_rels.apply(lambda row: get_unique_id(row, 'target'), axis=1)

# 1.12 custom order columns for readability
node_cols = ["name", "label", "location_country", "location_city", "amount", "status", "phase", "id", "article_id", "unique_id"]
rels_cols = ["type", "group", "source_label", "target_label", "source", "target", "article_id", "id"]

# 1.13: Save raw flattened node and relationship data to Excel
df_all_nodes.to_excel("storage/output/all_nodes.xlsx", 
                          columns=node_cols,
                          index=False)
df_all_rels.to_excel("storage/output/all_rels.xlsx",
                            columns=rels_cols,
                            index=False)

