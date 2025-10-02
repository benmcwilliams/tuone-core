from typing import Tuple, Dict
import pandas as pd
from src.load_geo_lookup import build_geo_lookup

# split df_all_nodes into filtered views containing each node label type

def filter_nodes_by_label(df_nodes):
    return {
        "joint_venture": df_nodes[df_nodes["label"].str.lower() == "joint_venture"],
        "factory": df_nodes[df_nodes["label"].str.lower().str.contains("factory", na=False)].copy(),
        "capacity": df_nodes[df_nodes["label"].str.lower() == "capacity"],
        "product": df_nodes[df_nodes["label"].str.lower() == "product"],
        "company": df_nodes[df_nodes["label"].str.lower() == "company"],
        "investment": df_nodes[df_nodes["label"].str.lower() == "investment"],
        "owner": df_nodes[df_nodes["label"].str.lower().isin(["company", "joint_venture"])]
    }

# split df_all_rels into filtered views containing each relationship type

def filter_rels_by_label(df_rels):
    return {
        "owns": df_rels[df_rels["type"].str.lower() == "owns"],                 #ownership
        "forms": df_rels[df_rels["type"].str.lower() == "forms"],                #ownership
        "at": df_rels[df_rels["type"].str.lower() == "at"],                     #technological
        "produced_at": df_rels[df_rels["type"].str.lower() == "produced_at"],   #technological
        "quantifies": df_rels[df_rels["type"].str.lower() == "quantifies"],     #technological
        "funds": df_rels[df_rels["type"].str.lower() == "funds"],               #financial-technological   
        "targets": df_rels[df_rels["type"].str.lower() == "targets"],           #financial-technological
        "enables": df_rels[df_rels["type"].str.lower() == "enables"],           #financial-technological
        "invests": df_rels[df_rels["type"].str.lower() == "invests"],           #financial-origin
        "receives": df_rels[df_rels["type"].str.lower() == "receives"]          #financial-origin
    }

# load the context needed for our views

def make_context_from_frames(df_all_nodes: pd.DataFrame,
                             df_all_rels: pd.DataFrame
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame], dict]:
    """Build the (nodes_by_label, rels_by_label, geo_lookup) context from in-memory DataFrames."""
    geo_lookup = build_geo_lookup()
    nodes_by_label = filter_nodes_by_label(df_all_nodes)
    rels_by_label  = filter_rels_by_label(df_all_rels)
    return nodes_by_label, rels_by_label, geo_lookup