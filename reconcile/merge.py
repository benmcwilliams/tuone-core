import sys; sys.path.append("..")
import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple
from functools import lru_cache

from src.merge_helpers import filter_nodes_by_label, filter_rels_by_label
from src.geonames_helpers import clean_city, clean_country, normalize_city_key
from src.step_2 import standardize_country
from src.load_geo_lookup import build_geo_lookup, get_geo_value
from src.config import ALL_NODES, ALL_RELS, FACTORY_TECH
from src.merge_specifications import FACTORY_TECH_SPEC, COMPANY_FORMS_JV_SPEC, INVESTMENT_FUNDS_SPEC
from src.config import FACTORY_TECH, COMPANY_JV, INVESTMENT_FUNDS
from src.debug_helpers import get_debug_tracker

# ---- Context type ----
Context = Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame], dict]
# (nodes_by_label, rels_by_label, geo_lookup)

# ---------- helper functions ----------

def expand_nodes(nodes_by_label: Dict[str, pd.DataFrame],
                 label: str,
                 keep_cols: List[str],
                 rename: Dict[str, str]) -> pd.DataFrame:
    if isinstance(label, list):
        dfs = [nodes_by_label[l].copy() for l in label]
        df = pd.concat(dfs, ignore_index=True)
    else:
        df = nodes_by_label[label].copy()

    # Ensure all keep_cols exist
    for col in keep_cols:
        if col not in df.columns:
            # Decide default based on column semantics
            if col in ["is_total"]:  
                df[col] = False   # ✅ sensible default
            else:
                df[col] = None    # generic fallback

    return df.loc[:, keep_cols].rename(columns=rename)

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
               geo_lookup=None,
               view_name: Optional[str] = None,
               debug_article_id: Optional[str] = None) -> pd.DataFrame:
    """
    view_spec keys:
      - "nodes": { "<alias>": { "label": ..., "keep": [...], "rename": {...}, "enrich": Optional[Callable] } }
      - "edges": [ { "alias": ..., "type": ..., "source_label": ..., "target_label": ..., "rename": {...} } ]
      - "join_chain": [ ("edges_alias_or_node_alias", "key_left", "node_alias", "key_right", "how") ...]
      - "filters": [ Callable[[pd.DataFrame], pd.DataFrame], ... ]
      - "column_order": Optional[List[str]]
    """
    tracker = get_debug_tracker() if debug_article_id else None
    use_debug = tracker is not None and tracker.article_id == debug_article_id

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
    start_alias = view_spec["join_chain"][0][0]
    df = tables[start_alias]
    for step_idx, (left_alias, key_left, right_alias, key_right, how) in enumerate(view_spec["join_chain"]):
        left_df = df if left_alias == start_alias else tables[left_alias]
        right_df = tables[right_alias]
        before_count = None
        if use_debug and "article_id" in df.columns:
            sub = df[df["article_id"] == debug_article_id]
            before_count = len(sub)
        df = left_df.merge(right_df, left_on=key_left, right_on=key_right, how=how)
        if use_debug and "article_id" in df.columns:
            after_count = len(df[df["article_id"] == debug_article_id])
            join_desc = f"{left_alias}.{key_left} x {right_alias}.{key_right} ({how})"
            stage = f"{view_name or 'view'}_join_{step_idx}" if view_name else f"join_{step_idx}"
            tracker.checkpoint(stage, after_count, join_desc)
            if before_count is not None and before_count > 0 and after_count == 0 and how == "inner":
                tracker.drop_reason(
                    stage,
                    "all rows for this article dropped at inner join",
                    f"Join {join_desc}: left had %d rows for article but no matching keys on right (e.g. missing ownership or relationship path)." % before_count,
                )

    # 4) filters
    for f in view_spec.get("filters", []):
        before_filter = len(df[df["article_id"] == debug_article_id]) if (use_debug and "article_id" in df.columns) else 0
        if use_debug and "article_id" in df.columns and before_filter > 0 and "iso2" in df.columns:
            iso2_vals = df.loc[df["article_id"] == debug_article_id, "iso2"].dropna().unique().tolist()
            tracker.info("Before EU filter: article rows=%d, iso2 values=%s", before_filter, iso2_vals)
        df = f(df)
        if use_debug and "article_id" in df.columns:
            after_filter = len(df[df["article_id"] == debug_article_id])
            if before_filter > 0 and after_filter == 0:
                tracker.drop_reason(
                    "EU_filter",
                    "all article rows removed by EU country filter (iso2 not in EUROPEAN_COUNTRIES)",
                    "Add or fix location/country so facilities resolve to an EU country code.",
                )

    # 5) column order
    if "column_order" in view_spec and view_spec["column_order"]:
        cols = [c for c in view_spec["column_order"] if c in df.columns]
        df = df.loc[:, cols]

    return df

def run_view(spec, out_path=None, *, context: Context, view_name: Optional[str] = None):
    """Build the view using an explicit in-memory context (required)."""
    nodes_by_label, rels_by_label, geo_lookup = context
    tracker = get_debug_tracker()
    debug_article_id = tracker.article_id if tracker else None
    df = build_view(
        spec,
        nodes_by_label,
        rels_by_label,
        geo_lookup=geo_lookup,
        view_name=view_name,
        debug_article_id=debug_article_id,
    )
    if out_path:
        df.to_excel(out_path, index=False)  # keep optional export for humans
        logging.info(f"💾 Saved: {out_path}")
    return df

if __name__ == "__main__":
    # Intentionally no implicit context here.
    # Build a context in your orchestrator and call run_view(..., context=ctx)
    logging.info("This module requires an explicit `context` now.")
