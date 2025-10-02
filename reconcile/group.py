import sys; sys.path.append("..")
from datetime import datetime
import logging
import pandas as pd
import numpy as np
import uuid
from src.id_date_dict import get_article_id_to_date_map
from src.company_mapping import map_to_canonical, SITE_MERGE
from src.inputs import EUROPEAN_COUNTRIES
from src.config import COMPANY_JV
from src.set_adm_level import add_admin_group_key

def group_projects(file_to_group, out_path, output_cols):

    # 1) Load (EU-only) and drop required fields with consistent logging
    df = pd.read_excel(file_to_group)
    df = df[df["iso2"].isin(EUROPEAN_COUNTRIES)].copy()
    initial_len = len(df)
    logging.info(f"Found {len(df)} rows (EU only).")

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
            logging.info(f"⚠️ {missing} entries without {desc} are dropped.")
        before = len(df)
        df = df.dropna(subset=[col])
        if len(df) != before:
            logging.info(f"Rows reduced to {len(df)} after dropping missing {col}.")

    missing_product_lv2 = df["product_lv2"].isna().sum()
    logging.info(f"⚠️ {initial_len - len(df)} total rows dropped due to missing required fields; {len(df)} remain.")
    logging.info(f"⚠️ {missing_product_lv2} entries without a normalised PRODUCT-LV2.")

    # apply any manual company or joint venture name mapping
    logging.info(f"Unique owners before manual dict: {len(df['inst_canon'].unique())}")
    df['inst_canon'] = df['inst_canon'].apply(map_to_canonical)
    logging.info(f"Unique owners after manual dict: {len(df['inst_canon'].unique())}")

    # apply any manual site merges (eg CATL erfurt to CATL arnstadt)
    # NOTE this happens before joint venture mapping
    # we update admin_group_key which is the ADM level we are using per country

    def _site_merge(row):
        key = (row["inst_canon"], row["iso2"], row["admin_group_key"])
        return SITE_MERGE.get(key, row["admin_group_key"])

    before = df["admin_group_key"].copy()
    df["admin_group_key"] = df.apply(_site_merge, axis=1)
    n_changed = (df["admin_group_key"] != before).sum()
    logging.info(f"Applied site merges to {n_changed} rows.")

    ### HACKY FIX SO CODE WORKS WITH ROSS TO BE UDPATED *****
    df["adm1-og"] = df["adm1"]
    df["adm1"] = df["admin_group_key"]

    # 2. Resolve Joint Venture cases
    cjv = pd.read_excel(COMPANY_JV, dtype=str)
    cjv["company_canon_norm"] = cjv["company_canon"].apply(map_to_canonical)            # normalise company and JVs as we do above (manual names)
    cjv["jv_canon_norm"] = cjv["jv_canon"].apply(map_to_canonical)                      # normalise company and JVs as we do above (manual names)

    # build: JV name (normalized) -> sorted unique list of member companies (normalized)
    jv_to_members = (
        cjv.groupby("jv_canon_norm")["company_canon_norm"]
           .apply(lambda s: sorted(x for x in set(s) if isinstance(x, str) and x.strip()))
           .to_dict()
    )

    # for JVs → list of member companies; for companies → singleton list
    def _members_for_owner(owner: str):
        if isinstance(owner, str):
            return jv_to_members.get(owner, [owner])
        return []

    # --- build hashable owner key (JV → members; company → singleton) ---
    df["inst_canon_multiple"] = df["inst_canon"].apply(_members_for_owner)
    df["owner_key"] = df["inst_canon_multiple"].apply(tuple)    # hashable

    # Promote member-only owner_keys to JV owner_keys within the same place/product context
    jv_context_cols = ["adm1", "product_lv1"]  # context cols for determining a JV

    def _promote_ctx(g):
        jv_rows = g[g["inst_type"] == "joint_venture"]
        if jv_rows.empty:
            return g
        # map singleton member keys → the JV key observed in this context
        mapping = {}
        for jv_key in jv_rows["owner_key"].unique():
            for m in jv_key:
                mapping.setdefault((m,), jv_key)  # first JV wins deterministically
        mask_singleton_member = (g["inst_type"] == "company") & g["owner_key"].isin(mapping.keys())
        if mask_singleton_member.any():
            g.loc[mask_singleton_member, "owner_key"] = g.loc[mask_singleton_member, "owner_key"].map(mapping)
        return g

    df = df.groupby(jv_context_cols, group_keys=False).apply(_promote_ctx)

    # (optional) pretty display name: JV label if known, else join members
    members_to_jv = {tuple(v): k for k, v in jv_to_members.items()}
    df["owner_label"] = df["owner_key"].apply(lambda t: members_to_jv.get(tuple(t), " + ".join(t)))

    # Generate hash key - stable namespace for reproducibility
    NS = uuid.uuid5(uuid.NAMESPACE_URL, "bruegel/project-key/v1")

    # build the tuple
    df["project_key_tuple"] = list(
        zip(
            df["iso2"].astype(str),
            df["adm1"].astype(str),
            df["owner_key"].astype(str),
            df["product_lv1"].astype(str),
        )
    )

    # readable string
    df["project_key_str"] = df["project_key_tuple"].apply(lambda t: "|".join(map(str, t)))

    # deterministic UUID5 hash
    df["project_id"] = df["project_key_str"].apply(lambda s: str(uuid.uuid5(NS, s)))

    # 3) Compute clusters

    # DEFINE group cols 
    group_cols = [
        "adm1",   #NOTE to be replaced with admin_group_key
        "owner_key",          
        #"inst_canon",
        "product_lv1"
    ]

    complete_mask = df[group_cols].notna().all(axis=1)
    df['cluster_num'] = np.nan 
    df['cluster_id']  = '000000'
    tmp = df.loc[complete_mask].copy()
    tmp['cluster_num'] = tmp.groupby(group_cols).ngroup() + 1
    sizes = tmp.groupby('cluster_num')['factory'].transform('size')

    tmp['cluster_id'] = (
        sizes.gt(0)                       # keep all clusters with ≥0 rows
        .mul(tmp['cluster_num'])          # multiply to keep the number or 0
        .astype(int)
        .astype(str)
        .str.zfill(6)                     # pad to six digits
    )
    df.loc[complete_mask, ['cluster_num', 'cluster_id']] = tmp[['cluster_num', 'cluster_id']]

    # 4) Clean and save output

    # set and sort by datetime, cluster_id
    id_to_date = get_article_id_to_date_map()   # map article dates
    
    df['date'] = df['article_id'].map(id_to_date)
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m', errors='coerce')
    df.sort_values(by=["cluster_id", "date"], na_position='last', inplace=True)
    df['date'] = df['date'].dt.strftime('%Y-%m')

    # hacky fix until I tell Ross to change
    df.loc[df["inst_type"] == "joint_venture", "inst_canon"] = df.loc[df["inst_type"] == "joint_venture", "owner_label"]
    logging.info(f"Overwrote inst_canon with JV labels for {sum(df['inst_type']=='joint_venture')} rows")

    df[output_cols].to_excel(out_path, index=False)
    logging.info(f"Saving filtered output to {out_path}")
