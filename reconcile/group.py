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

def group_projects(file_to_group, out_path, output_cols):

    # 1) Load (EU-only) and drop required fields with consistent logging
    df = pd.read_excel(file_to_group)
    df = df[df["iso2"].isin(EUROPEAN_COUNTRIES)].copy()
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
        before = len(df)
        df = df.dropna(subset=[col])
        if len(df) != before:
            logging.info(f"Rows reduced to {len(df)} after dropping missing {col}.")

    missing_product_lv2 = df["product_lv2"].isna().sum()
    logging.info(f"⚠️ {initial_len - len(df)} total rows dropped due to missing required fields; {len(df)} remain.")
    logging.debug(f"⚠️ {missing_product_lv2} entries without a normalised PRODUCT-LV2.")

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

    # 3. Apply manual JV merging

    def _jv_merge(row):
        key = (row["inst_canon"], row["iso2"], row["admin_group_key"], row["product_lv1"])
        return JV_MERGE.get(key, row["inst_canon"])

    # Keep an audit column, then apply
    df["inst_canon_premerge"] = df["inst_canon"]
    df["inst_canon"] = df.apply(_jv_merge, axis=1)

    n_changed = (df["inst_canon"] != df["inst_canon_premerge"]).sum()
    logging.info(f"Applied JV merges to {n_changed} rows (exact match only).")

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

    # 3) Compute clusters

    # # DEFINE group cols 
    # group_cols = [
    #     "admin_group_key",         
    #     "inst_canon",
    #     "product_lv1"
    # ]

    # complete_mask = df[group_cols].notna().all(axis=1)
    # df['cluster_num'] = np.nan 
    # df['cluster_id']  = '000000'
    # tmp = df.loc[complete_mask].copy()
    # tmp['cluster_num'] = tmp.groupby(group_cols).ngroup() + 1
    # sizes = tmp.groupby('cluster_num')['factory'].transform('size')

    # tmp['cluster_id'] = (
    #     sizes.gt(0)                       # keep all clusters with ≥0 rows
    #     .mul(tmp['cluster_num'])          # multiply to keep the number or 0
    #     .astype(int)
    #     .astype(str)
    #     .str.zfill(6)                     # pad to six digits
    # )
    # df.loc[complete_mask, ['cluster_num', 'cluster_id']] = tmp[['cluster_num', 'cluster_id']]

    # 4) Clean and save output

    # set and sort by datetime, cluster_id
    id_to_date = get_article_id_to_date_map()   # map article dates
    
    df['date'] = df['article_id'].map(id_to_date)
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m', errors='coerce')
    df.sort_values(by=["project_id", "date"], na_position='last', inplace=True)
    df['date'] = df['date'].dt.strftime('%Y-%m')

    df[output_cols].to_excel(out_path, index=False)
    logging.info(f"Saving filtered output to {out_path}")

from src.config import (
    FACTORY_REGISTRY,
    GROUPED_FACTORIES,
    grouped_facilities_cols)

if __name__ == "__main__":
    group_projects(FACTORY_REGISTRY,  GROUPED_FACTORIES, grouped_facilities_cols)
