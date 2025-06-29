import sys; sys.path.append("..")  # allow access to parent folder modules
import pandas as pd
from openpyxl import Workbook, load_workbook
from functools import reduce
from mongo_client import mongo_client, articles_collection
from reconcile.src.merge_helpers import deduplicate_nodes_and_rels, filter_nodes_by_label, filter_rels_by_label

## file outputs a clean factory-technology file, this includes all cases of 
## owner | factory | capacity | product

# config
output_file = "storage/output/factory-technological.xlsx"
nodes_input = "storage/output/all_nodes.xlsx"
rels_input = "storage/output/all_rels.xlsx"

## 1.1 Basic set up 
#  read nodes and relationships
df_all_nodes = pd.read_excel(nodes_input)
df_all_rels = pd.read_excel(rels_input)

# deduplicate raw data
df_all_nodes, df_all_rels = deduplicate_nodes_and_rels(df_all_nodes, df_all_rels)

# set nodes and relationships subsets
nodes = filter_nodes_by_label(df_all_nodes)
rels = filter_rels_by_label(df_all_rels)

## 1.2 Compile relevant node metadata
# for factory: name, city, country
df_factory_expand = nodes["factory"][[
    "name", "unique_id", "location_factory_city_adm3_name", "location_country_standardized", "article_id"
]].rename(columns={
    "unique_id": "factory_id",
    "location_factory_city_adm3_name": "adm3",          # replace with geonames once I run on main collection
    "location_country_standardized": "country",         # replace with geonames once I run on main collection
    "name": "factory"
})

# for capacity: amount, status, phase
df_capacity_expand = nodes["capacity"][[
    "amount", "unique_id", "status", "phase"
]].rename(columns={
    "unique_id": "capacity_id",
    "amount": "capacity"
})

# for product: name
df_product_expand = nodes["product"][[
    "name", "unique_id",
]].rename(columns={
    "unique_id": "product_id",
    "name": "product"
})

# for owner (company | joint venture): name
df_owner_expand = nodes["owner"][[
    "name", "unique_id",
]].rename(columns={
    "unique_id": "owner_id",
    "name": "institution"
})

## 1.3 Clean formatting for each relationship type 
# for "QUANTIFY" relationship
clean_quantifies = rels["quantifies"][
    (rels["quantifies"]["source_label"] == "capacity") &
    (rels["quantifies"]["target_label"] == "product")
]

df_quant = (
    clean_quantifies
      .loc[:, ["source", "target"]]
      .rename(columns={"source": "capacity_id",  "target": "product_id"})
)

# for "AT" relationship
clean_at = rels["at"][
    (rels["at"]["source_label"] == "capacity") &
    (rels["at"]["target_label"] == "factory")
]

df_at = (
    clean_at
      .loc[:, ["source", "target"]]
      .rename(columns={"source": "capacity_id",  "target": "factory_id"})
)

# for "OWNS" relationship 

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

## 1.4. Merge and output 

df_capacity_product = df_quant.merge(df_at, on="capacity_id", how="inner")

df_all = df_owns.merge(df_capacity_product, on = "factory_id")

enrich_factory = df_all.merge(df_factory_expand, on = "factory_id")
enrich_capacity = enrich_factory.merge(df_capacity_expand, on = "capacity_id")
enrich_owner = enrich_capacity.merge(df_owner_expand, on = "owner_id")
enrich_product = enrich_owner.merge(df_product_expand, on = "product_id")

custom_order = ["article_id", "institution", "factory", "country", "adm3", "capacity", "product", "phase", "status"]

enrich_product.to_excel(output_file,
                        columns=custom_order,
                        index=False)

print(f"Success. Output written to {output_file}")