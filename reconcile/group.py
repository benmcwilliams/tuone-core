import sys; sys.path.append("..")
from datetime import datetime
import logging
import pandas as pd
import numpy as np
import uuid
from src.id_date_dict import get_article_id_to_date_map
from src.company_mapping import map_to_canonical, SITE_MERGE, JV_MERGE
from src.inputs import EUROPEAN_COUNTRIES
from src.config import COMPANY_JV
from src.set_adm_level import add_admin_group_key
from src.debug_helpers import debug_print_df, get_debug_tracker


def _article_row_count(df: pd.DataFrame, article_id: str | None) -> int:
    if not article_id or "article_id" not in df.columns or df.empty:
        return 0
    return int((df["article_id"] == article_id).sum())


def group_projects(file_to_group: pd.DataFrame | str, out_path, output_cols, debug_article_id: str | None = None) -> pd.DataFrame:

    tracker = get_debug_tracker()
    use_debug = tracker is not None and debug_article_id and tracker.article_id == debug_article_id

    # 1) Load (EU-only) and drop required fields with consistent logging
    if isinstance(file_to_group, pd.DataFrame):
        df = file_to_group.copy()
    else:
        df = pd.read_excel(file_to_group)
    df = df[df["iso2"].isin(EUROPEAN_COUNTRIES)].copy()
    if "product_lv3" not in df.columns:
        df["product_lv3"] = None
    if use_debug:
        n = _article_row_count(df, debug_article_id)
        tracker.section("Grouping: %s" % (out_path or "table"))
        tracker.checkpoint("after_EU_filter", n, "input to this grouping step")
        if n == 0:
            tracker.drop_reason(
                "grouping_input",
                "no rows for this article in the input table",
                "Upstream merge or registry already had 0 rows for this article (e.g. EU filter or join chain removed them).",
            )
    debug_print_df(
        df,
        label=f"{out_path} / raw_eu",
        cols=[
            "article_id",
            "inst_canon",
            "inst_type",
            "iso2",
            "factory",
            "admin_group_key",
            "product_lv1",
            "product_lv2",
            "product_lv3",
            "factory_status",
            "city_key",
        ],
        debug_article_id=debug_article_id,
    )
    initial_len = len(df)
    logging.debug(f"Found {len(df)} rows (EU only).")

    # build unified region key based on per-country admin level
    df = add_admin_group_key(df, out_col="admin_group_key")

    required = [
        ("inst_canon",              "a normalised OWNER name"),
        ("city_key",                "CITY"),
        ("admin_group_key",         "a geographic locator"),
        ("product_lv1",             "a normalised PRODUCT-LV1"),
    ]

    for col, desc in required:
        missing = df[col].isna().sum()
        if missing:
            logging.debug(f"⚠️ {missing} entries without {desc} are dropped.")
        before_count = _article_row_count(df, debug_article_id) if use_debug else 0
        before = len(df)
        df = df.dropna(subset=[col])
        if len(df) != before:
            logging.debug(f"Rows reduced to {len(df)} after dropping missing {col}.")
        if use_debug:
            after_count = _article_row_count(df, debug_article_id)
            if before_count > 0 and after_count == 0:
                tracker.drop_reason(
                    "required_field",
                    "all article rows dropped due to missing required field: %s" % col,
                    desc,
                )
            tracker.checkpoint("after_drop_%s" % col, after_count, desc)

    missing_product_lv2 = df["product_lv2"].isna().sum()
    missing_product_lv3 = df["product_lv3"].isna().sum()
    logging.debug(f"⚠️ {initial_len - len(df)} total rows dropped due to missing required fields; {len(df)} remain.")
    logging.debug(f"⚠️ {missing_product_lv2} entries without a normalised PRODUCT-LV2.")
    logging.debug(f"⚠️ {missing_product_lv3} entries without a normalised PRODUCT-LV3.")

    # apply any manual company or joint venture name mapping
    logging.debug(f"Unique owners before manual dict: {len(df['inst_canon'].unique())}")

    df['inst_canon'] = df['inst_canon'].apply(map_to_canonical)
    logging.debug(f"Unique owners after manual dict: {len(df['inst_canon'].unique())}")

    # 2. Apply manual site merges (eg collapse CATL’s nearby German sites to one admin key | Erfurt → Arnstadt)
    def _site_merge(row):
        key = (row["inst_canon"], row["iso2"], row["admin_group_key"])
        return SITE_MERGE.get(key, row["admin_group_key"])

    before = df["admin_group_key"].copy()
    df["admin_group_key"] = df.apply(_site_merge, axis=1)
    n_changed = (df["admin_group_key"] != before).sum()
    logging.debug(f"Applied site merges to {n_changed} rows.")

    debug_print_df(
        df,
        label=f"{out_path} / after_site_merges",
        cols=[
            "article_id",
            "inst_canon",
            "inst_type",
            "iso2",
            "factory",
            "admin_group_key",
            "product_lv1",
            "product_lv2",
            "product_lv3",
            "factory_status",
        ],
        debug_article_id=debug_article_id,
    )

    # 3. Apply manual JV merging

    def _jv_merge(row):
        key = (row["inst_canon"], row["iso2"], row["admin_group_key"], row["product_lv1"])
        return JV_MERGE.get(key, row["inst_canon"])

    # Keep an audit column, then apply
    df["inst_canon_premerge"] = df["inst_canon"]
    df["inst_canon"] = df.apply(_jv_merge, axis=1)

    n_changed = (df["inst_canon"] != df["inst_canon_premerge"]).sum()
    logging.debug(f"Applied JV merges to {n_changed} rows (exact match only).")

    debug_print_df(
        df,
        label=f"{out_path} / after_jv_merges",
        cols=[
            "article_id",
            "inst_canon",
            "inst_type",
            "iso2",
            "factory",
            "admin_group_key",
            "product_lv1",
            "product_lv2",
            "product_lv3",
            "factory_status",
        ],
        debug_article_id=debug_article_id,
    )

    # Generate hash key - stable namespace for reproducibility
    NS = uuid.uuid5(uuid.NAMESPACE_URL, "bruegel/project-key/v1")

    # build the tuple
    df["project_key_tuple"] = list(
        zip(
            df["iso2"].astype(str),
            df["admin_group_key"].astype(str),
            df["inst_canon"].astype(str),
            df["product_lv1"].astype(str),
        )
    )

    # readable string
    df["project_key_str"] = df["project_key_tuple"].apply(lambda t: "|".join(map(str, t)))

    # deterministic UUID5 hash
    df["project_id"] = df["project_key_str"].apply(lambda s: str(uuid.uuid5(NS, s)))

    # 4) Apply any custom filters

    # For rows where product_lv1 == "iron", keep only those where product_lv2 is in ["DRI", "hydrogen DRI", "natural gas DRI"]
    before_product_filter = _article_row_count(df, debug_article_id) if use_debug else 0
    allowed_lv2 = ["DRI", "hydrogen DRI", "natural gas DRI"]
    mask = ~(
        (df["product_lv1"] == "iron") &
        (~df["product_lv2"].isin(allowed_lv2))
    )
    df = df[mask].copy()
    # Additionally, for the kept rows where product_lv1 == "iron" and lv2 is in allowed_lv2, set lv2 to 'DRI'
    iron_mask = (df["product_lv1"] == "iron") & (df["product_lv2"].isin(allowed_lv2))
    df.loc[iron_mask, "product_lv2"] = "DRI"
    if use_debug:
        after_product_filter = _article_row_count(df, debug_article_id)
        tracker.checkpoint("after_product_lv2_filters", after_product_filter)
        if before_product_filter > 0 and after_product_filter == 0:
            tracker.drop_reason("product_lv2_filter", "all article rows removed by iron/DRI product_lv2 filter", None)
        final_n = after_product_filter
        if final_n == 0:
            tracker.add_diagnosis_bullet("Final row count for this article in this table: 0. See drop reasons above (EU filter, join chain, or required fields).")

    debug_print_df(
        df,
        label=f"{out_path} / after_product_lv2_filters",
        cols=[
            "article_id",
            "inst_canon",
            "inst_type",
            "iso2",
            "factory",
            "admin_group_key",
            "product_lv1",
            "product_lv2",
            "product_lv3",
            "factory_status",
            "project_id",
        ],
        debug_article_id=debug_article_id,
    )

    # 4) Clean and save output

    # set and sort by datetime, cluster_id
    id_to_date = get_article_id_to_date_map()   # map article dates
    
    df['date'] = df['article_id'].map(id_to_date)
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m', errors='coerce')
    df.sort_values(by=["project_id", "date"], na_position='last', inplace=True)
    df['date'] = df['date'].dt.strftime('%Y-%m')

    result = df[output_cols].copy()
    result.to_excel(out_path, index=False)
    logging.info(f"Saving filtered output to {out_path}")
    return result

from src.config import (
    FACTORY_REGISTRY,
    GROUPED_FACTORIES,
    grouped_facilities_cols)

if __name__ == "__main__":
    group_projects(FACTORY_REGISTRY,  GROUPED_FACTORIES, grouped_facilities_cols)
