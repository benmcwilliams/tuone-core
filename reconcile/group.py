import sys; sys.path.append("..")
from datetime import datetime
import logging
import pandas as pd
import numpy as np
import pprint
from src.id_date_dict import get_article_id_to_date_map
from src.company_mapping import map_to_canonical
from src.inputs import EUROPEAN_COUNTRIES
from src.config import FACTORY_TECH, FACTORY_TECH_CLEAN_CAPACITIES, GRPD_PROJECTS, GRPD_PROJECTS_FILTER

def group_projects():

    # DEFINE subset cols 
    group_cols = [
        "adm1",             
        "inst_canon",
        "product_lv1"
    ]

    # 1) Load and validate data
    df = pd.read_excel(FACTORY_TECH_CLEAN_CAPACITIES)
    df = df[(df["iso2"].isin(EUROPEAN_COUNTRIES))].copy() # only filter applied is European for now. 
    initial_len = len(df)
    logging.info(f"Found {initial_len} rows:")

    # dropping missing cities
    missing_cities = df["city_key"].isna().sum()
    df = df.dropna(subset=['city_key'])
    logging.info(f"⚠️ {missing_cities} entries without CITY are dropped, rows reduced to {len(df)}.")

    # count missing values per column before dropping
    missing_counts = df[group_cols + ["product_lv2"]].isna().sum()
    logging.info(f"Missing counts: {pprint.pformat(missing_counts, indent=2)}")

    df = df.dropna(subset=group_cols)
    logging.info(f"⚠️  {initial_len - len(df)} rows dropped because of missing values; {len(df)} remain.")

    # apply temporary manual company name mapping
    logging.info(f"Unique owners before manual dict: {len(df["inst_canon"].unique())}")
    df['inst_canon'] = df['inst_canon'].apply(map_to_canonical)
    logging.info(f"Unique owners after manual dict: {len(df["inst_canon"].unique())}")

    if df.empty:
        logging.error("No valid rows remaining after validation. Exiting.")
        sys.exit(1)

    # 2) Replace ADM1 with ADM2 for iso2 == GB (because ADM1 is England, Scotland for GB)

    mask = (df['iso2'] == "GB") & (df['adm2'].notna())
    df.loc[mask, 'adm1'] = df.loc[mask, 'adm2']

    # 3) Compute clusters

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

    # custom column names

    cols = ["inst_canon", "city_key", "adm1", "adm2", "iso2", "bbox", "cluster_id",
            "product_lv1", "product_lv2", "product",
            "capacity_normalized", "capacity_metric_normalized",
            "status", "phase", "date", "article_id"]

    df.to_excel(GRPD_PROJECTS_FILTER, columns=cols, index=False)
    logging.info(f"Saving filtered output to {GRPD_PROJECTS_FILTER}")
