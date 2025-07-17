import sys; sys.path.append("..")
from datetime import datetime
import time
import logging
import pandas as pd
import numpy as np
from reconcile.src.id_date_dict import get_article_id_to_date_map
from normalise_capacity import run_extraction_pipeline
from src.inputs import EUROPEAN_COUNTRIES
from manual_companies import map_to_canonical

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/pipeline_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Start timing the entire pipeline
t0_pipeline = time.time()

# Input file and columns to validate
file_path = "./storage/output/factory-technological.xlsx"
output_file_long = "./storage/output/all_projects.xlsx"
output_file_filtered = "storage/output/filtered_projects_jul16.xlsx"

# DEFINE subset cols 
group_cols = [
    "adm1",             
    "inst_canon",
    "product_lv1"
]

# 1) Load and validate data
logging.info(f"Reading input file: {file_path}")
df = pd.read_excel(file_path)
initial_len = len(df)

# count missing values per column before dropping
missing_counts = df[group_cols].isna().sum()
logging.info("Missing values per column before dropping:")
logging.info(missing_counts)

df = df.dropna(subset=group_cols)
logging.info(f"Dropped {initial_len - len(df)} rows; {len(df)} remain after validation")

# apply temporary manual company name mapping
print(f"Unique owners before manual dict: {len(df["inst_canon"].unique())}")
df['inst_canon'] = df['inst_canon'].apply(map_to_canonical)
print(f"Unique owners after manual dict: {len(df["inst_canon"].unique())}")

if df.empty:
    logging.error("No valid rows remaining after validation. Exiting.")
    sys.exit(1)

# 2a) Normalise capacities 

df = run_extraction_pipeline(df)

# 2b) Replace ADM1 with ADM2 for iso2 == GB (because ADM1 is England, Scotland for GB)

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

cols = ["inst_canon", "city_key", "adm1", "adm2", "iso2", "cluster_id",
        "product_lv1", "product_lv2", "product",
        "capacity_normalized", "capacity_metric_normalized",
        "status", "phase", "date", "article_id"]

logging.info(f"Saving output to {output_file_long}")
df.to_excel(output_file_long, columns=cols, index=False)

# battery projects to validate
df_filter = df[(df["product_lv1"] == "battery") & (df["product_lv2"] != "eam") & (df["iso2"].isin(EUROPEAN_COUNTRIES))].copy()
df_filter.to_excel(output_file_filtered, columns = cols, index=False)

# Final timing
t1_pipeline = time.time()
logging.info(f"Total pipeline time: {(t1_pipeline - t0_pipeline)/60:.2f} minutes")
