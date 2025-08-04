import sys; sys.path.append("..")  # allow access to parent folder modules
import logging
import pandas as pd
from src.merge_helpers import deduplicate_nodes_and_rels, filter_nodes_by_label, filter_rels_by_label
from src.geonames_helpers import clean_city, clean_country, normalize_city_key
from src.step_2 import standardize_country
from src.load_geo_lookup import build_geo_lookup, get_geo_value
from src.config import ALL_NODES, ALL_RELS, FACTORY_TECH

## file outputs a clean factory-technology file, this includes all cases of 
## owner | factory | capacity | product

## 1.1 Basic set up 
#  read nodes and relationships

def merge_nodes_rels():

    df_all_nodes = pd.read_excel(ALL_NODES)
    df_all_rels = pd.read_excel(ALL_RELS)

    # build lookup dictionary
    geo_lookup = build_geo_lookup()

    # deduplicate raw data
    df_all_nodes, df_all_rels = deduplicate_nodes_and_rels(df_all_nodes, df_all_rels)

    # set nodes and relationships subsets
    nodes = filter_nodes_by_label(df_all_nodes)
    rels = filter_rels_by_label(df_all_rels)

    ## 1.2 Compile relevant node metadata

    # for factory: name, city, country
    df_factory_expand = nodes["factory"][[
        "name", "unique_id", "location_city", "location_country", "article_id"
    ]].rename(columns={
        "unique_id": "factory_id",
        "name": "factory"
    })

    # clean city name into city_key (compataible with mongo geonames collection)
    df_factory_expand["city_clean"] = df_factory_expand["location_city"].apply(clean_city)
    df_factory_expand["city_key"] = df_factory_expand["city_clean"].apply(normalize_city_key)

    # clean country into iso2 compatible with mongo geonames collection
    df_factory_expand["country_clean"] = df_factory_expand["location_country"].apply(clean_country)
    df_factory_expand["iso2"] = df_factory_expand["country_clean"].apply(lambda x: standardize_country(x)[1]) # returning only the iso2 value (out of three values returned)

    # query mongo geonames collection to return appropriate adm1
    df_factory_expand["adm1"] = df_factory_expand.apply(lambda row: get_geo_value(row, "adm1", geo_lookup), axis=1)
    df_factory_expand["adm2"] = df_factory_expand.apply(lambda row: get_geo_value(row, "adm2", geo_lookup), axis=1)
    df_factory_expand["bbox"] = df_factory_expand.apply(lambda row: get_geo_value(row, "bbox", geo_lookup), axis=1)

    # for capacity: amount, status, phase
    df_capacity_expand = nodes["capacity"][[
        "amount", "unique_id", "status", "phase"
    ]].rename(columns={
        "unique_id": "capacity_id",
        "amount": "capacity"
    })

    # for product: name, product_lv1, product_lv2
    df_product_expand = nodes["product"][[
        "name", "unique_id", "product_lv1", "product_lv2"
    ]].rename(columns={
        "unique_id": "product_id",
        "name": "product"
    })

    # for owner (company | joint venture): name
    df_owner_expand = nodes["owner"][[
        "name", "unique_id", "name_canon"
    ]].rename(columns={
        "unique_id": "owner_id",
        "name": "institution",
        "name_canon": "inst_canon"
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

    custom_order = ["article_id", "institution", "inst_canon", "factory", "city_key", "iso2", "adm1", "adm2", "bbox",
                    "capacity", "product", "product_lv1", "product_lv2", "phase", "status"]

    enrich_product.to_excel(FACTORY_TECH,
                            columns=custom_order,
                            index=False)

    logging.info(f"💾 Saved factory-technology graph segment to {FACTORY_TECH}")