import sys; sys.path.append("..")
import logging
import pandas as pd
from typing import Dict, List, Callable, Optional, Tuple

from src.merge_helpers import deduplicate_nodes_and_rels, filter_nodes_by_label, filter_rels_by_label
from src.geonames_helpers import clean_city, clean_country, normalize_city_key
from src.step_2 import standardize_country
from src.load_geo_lookup import build_geo_lookup, get_geo_value
from src.inputs import EUROPEAN_COUNTRIES
from src.config import ALL_NODES, ALL_RELS, FACTORY_TECH
from src.merge_specifications import FACTORY_REGISTRY_SPEC, FACTORY_TECH_SPEC, COMPANY_FORMS_JV_SPEC, INVESTMENT_FUNDS_SPEC
from src.config import FACTORY_REGISTRY, FACTORY_TECH, COMPANY_JV

# ---------- helper functions ----------

def expand_nodes(nodes_by_label: Dict[str, pd.DataFrame],
                 label: str,
                 keep_cols: List[str],
                 rename: Dict[str, str]) -> pd.DataFrame:
    if isinstance(label, list):
        dfs = [nodes_by_label[l].loc[:, keep_cols] for l in label]
        df = pd.concat(dfs, ignore_index=True)
    else:
        df = nodes_by_label[label].loc[:, keep_cols]
    return df.rename(columns=rename)

def extract_edge(rels_by_label: Dict[str, pd.DataFrame],
                 rel_type: str,
                 source_label: str,
                 target_label: str,
                 rename: Dict[str, str]) -> pd.DataFrame:
    df = rels_by_label[rel_type]
    if isinstance(source_label, list):
        df = df[df["source_label"].isin(source_label)]
    else:
        df = df[df["source_label"] == source_label]
    if isinstance(target_label, list):
        df = df[df["target_label"].isin(target_label)]
    else:
        df = df[df["target_label"] == target_label]
    return df.loc[:, ["source", "target"]].rename(columns=rename).drop_duplicates()

# ---------- Enrichers (pluggable) ----------

def enrich_factory_geo(df_factory: pd.DataFrame, geo_lookup) -> pd.DataFrame:
    # expects columns: location_city, location_country
    out = df_factory.copy()
    out["city_clean"] = out["location_city"].apply(clean_city)
    out["city_key"]  = out["city_clean"].apply(normalize_city_key)
    out["country_clean"] = out["location_country"].apply(clean_country)
    out["iso2"] = out["country_clean"].apply(lambda x: standardize_country(x)[1])
    # geo lookups (vectorized via apply keeps it simple; optimize later if needed)
    for col in ["adm1", "adm2", "adm3", "adm4", "bbox", "lat", "lon"]:
        out[col] = out.apply(lambda r: get_geo_value(r, col, geo_lookup), axis=1)
    return out


# ---------- View builder ----------

def build_view(view_spec: dict,
               nodes_by_label: Dict[str, pd.DataFrame],
               rels_by_label: Dict[str, pd.DataFrame],
               geo_lookup=None) -> pd.DataFrame:
    """
    view_spec keys:
      - "nodes": { "<alias>": { "label": ..., "keep": [...], "rename": {...}, "enrich": Optional[Callable] } }
      - "edges": [ { "alias": ..., "type": ..., "source_label": ..., "target_label": ..., "rename": {...} } ]
      - "join_chain": [ ("edges_alias_or_node_alias", "key_left", "node_alias", "key_right", "how") ...]
      - "filters": [ Callable[[pd.DataFrame], pd.DataFrame], ... ]
      - "dedupe": Optional[Tuple[List[str], str]]  # (subset_cols, keep)
      - "column_order": Optional[List[str]]
    """
    # 1) expand nodes
    node_tables = {}
    for alias, spec in view_spec["nodes"].items():
        df = expand_nodes(nodes_by_label, spec["label"], spec["keep"], spec["rename"])
        if spec.get("enrich"):
            df = spec["enrich"](df) if spec["enrich"] != "factory_geo" else enrich_factory_geo(df, geo_lookup)
        node_tables[alias] = df

    # 2) extract edges
    edge_tables = {}
    for e in view_spec.get("edges", []):
        edge_tables[e["alias"]] = extract_edge(
            rels_by_label, e["type"], e["source_label"], e["target_label"], e["rename"]
        )

    # 3) join chain
    tables = {**node_tables, **edge_tables}
    # tables holds all aliases and allows merges
    # start from the first element in the chain's left side
    start_alias = view_spec["join_chain"][0][0]
    df = tables[start_alias]
    for left_alias, key_left, right_alias, key_right, how in view_spec["join_chain"]:
        left_df = df if left_alias == start_alias else tables[left_alias]
        right_df = tables[right_alias]
        df = left_df.merge(right_df, left_on=key_left, right_on=key_right, how=how)

    # 4) filters
    for f in view_spec.get("filters", []):
        df = f(df)

    # 5) column order
    if "column_order" in view_spec and view_spec["column_order"]:
        cols = [c for c in view_spec["column_order"] if c in df.columns]
        df = df.loc[:, cols]

    return df

def run_view(spec, out_path=None):
    # 1) load raw
    df_all_nodes = pd.read_excel(ALL_NODES)
    df_all_rels  = pd.read_excel(ALL_RELS)
    #df_all_nodes, df_all_rels = deduplicate_nodes_and_rels(df_all_nodes, df_all_rels)

    # 2) normalize
    geo_lookup = build_geo_lookup()
    nodes_by_label = filter_nodes_by_label(df_all_nodes)
    rels_by_label  = filter_rels_by_label(df_all_rels)

    # 3) build
    df = build_view(spec, nodes_by_label, rels_by_label, geo_lookup=geo_lookup)

    if out_path:
        df.to_excel(out_path, index=False)
        logging.info(f"💾 Saved: {out_path}")
    return df

if __name__ == "__main__":
    #run_view(FACTORY_REGISTRY_SPEC, FACTORY_REGISTRY)
    #run_view(COMPANY_FORMS_JV_SPEC, COMPANY_JV)
    run_view(FACTORY_TECH_SPEC, FACTORY_TECH)
