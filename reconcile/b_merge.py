import sys; sys.path.append("..")  # allow access to parent folder modules
import pandas as pd
import os
import re
from openpyxl import Workbook, load_workbook
from functools import reduce
from src.to_pandas_helpers import flatten_dict
from mongo_client import mongo_client, articles_collection

def deduplicate_nodes_and_rels(df_nodes, df_rels):
    # remove duplicate rows by unique_id (nodes) and source-target-type triplet (rels)
    return (
        df_nodes.drop_duplicates(subset="unique_id"),
        df_rels.drop_duplicates(subset=["source", "target", "type"])
    )

def filter_nodes_by_label(df_nodes):
    # split df_all_nodes into filtered views containing each node label type
    return {
        "joint_venture": df_nodes[df_nodes["label"].str.lower() == "joint_venture"],
        "factory": df_nodes[df_nodes["label"].str.lower().str.contains("factory", na=False)].copy(),
        "capacity": df_nodes[df_nodes["label"].str.lower() == "capacity"],
        "product": df_nodes[df_nodes["label"].str.lower() == "product"],
        "company": df_nodes[df_nodes["label"].str.lower() == "company"],
        "investment": df_nodes[df_nodes["label"].str.lower() == "investment"]
    }

def filter_rels_by_label(df_rels):
    # split df_all_rels into filtered views containing each relationship type
    return {
        "owns": df_rels[df_rels["type"].str.lower() == "owns"],                 #ownership
        "forms": df_rels[df_rels["type"].str.lower() == "owns"],                #ownership
        "at": df_rels[df_rels["type"].str.lower() == "at"],                     #technological
        "produced_at": df_rels[df_rels["type"].str.lower() == "produced_at"],   #technological
        "quantifies": df_rels[df_rels["type"].str.lower() == "quantifies"],     #technological
        "funds": df_rels[df_rels["type"].str.lower() == "funds"],               #financial-technological   
        "targets": df_rels[df_rels["type"].str.lower() == "targets"],           #financial-technological
        "enables": df_rels[df_rels["type"].str.lower() == "enables"],           #financial-technological
        "invests": df_rels[df_rels["type"].str.lower() == "invests"],           #financial-origin
        "receives": df_rels[df_rels["type"].str.lower() == "receives"]          #financial-origin
    }

#  Run the pipeline
df_all_nodes = pd.read_excel("storage/output/all_nodes.xlsx")
df_all_rels = pd.read_excel("storage/output/all_rels.xlsx")

# deduplicate raw data
df_all_nodes, df_all_rels = deduplicate_nodes_and_rels(df_all_nodes, df_all_rels)

# break nodes and relationships into subsets
nodes = filter_nodes_by_label(df_all_nodes)
rels = filter_rels_by_label(df_all_rels)

# extract factory metadata: name, city, country
df_factory_expand = nodes["factory"][[
    "name", "unique_id", "location_city", "location_country"
]].rename(columns={
    "unique_id": "factory_id",
    "location_city": "factory_city",
    "location_country": "factory_country",
    "name": "factory_name"
})

# clean formatting for the "QUANTIFY" relationship
clean_quantifies = rels["quantifies"][
    (rels["quantifies"]["source_label"] == "capacity") &
    (rels["quantifies"]["target_label"] == "product")
]

df_quant = (
    clean_quantifies
      .loc[:, ["source", "target"]]
      .rename(columns={"source": "capacity_id",  "target": "product_id"})
)

# clean formatting for the "AT" relationship
clean_at = rels["at"][
    (rels["at"]["source_label"] == "capacity") &
    (rels["at"]["target_label"] == "factory")
]

df_at = (
    clean_at
      .loc[:, ["source", "target"]]
      .rename(columns={"source": "capacity_id",  "target": "factory_id"})
)

# clean formatting for the "OWNS" relationship 

clean_owns = rels["owns"][
    (rels["owns"]["source_label"].isin(["company", "joint_venture"])) &
    (rels["owns"]["target_label"] == "factory")
]

df_owns = (
    clean_owns
      .loc[:, ["source", "target"]]
      .rename(columns={"source": "owner_id",  "target": "factory_id"})
)

df_owns = df_owns.drop_duplicates(subset=["factory_id"], keep="first")     # kg should Never return duplicate owners - we should log cases where it happens and investigate

# merge and output 

df_capacity_product = df_quant.merge(df_at, on="capacity_id", how="inner")

df_all = df_owns.merge(df_capacity_product, on = "factory_id")
df_enrich = df_all.merge(df_factory_expand, on = "factory_id")
df_enrich.to_excel("storage/output/factory-technological.xlsx")

print("Success.")