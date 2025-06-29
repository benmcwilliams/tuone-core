import sys
from datetime import datetime
import time
import logging
import pandas as pd
from src.step_1 import TextCleaner

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

# DEFINE subset cols 

# subset_cols = [
#     "country_standardized",
#     "factory_city_adm3_name",
#     "owner_company_name",
#     "product_name"
# ]

# 1) Load and validate data
logging.info(f"Reading input file: {file_path}")
df = pd.read_excel(file_path, sheet_name="summary_view_factory")
initial_len = len(df)

df = df.dropna(subset=subset_cols)
logging.info(f"Dropped {initial_len - len(df)} rows; {len(df)} remain after validation")

if df.empty:
    logging.error("No valid rows remaining after validation. Exiting.")
    sys.exit(1)

# 2) Cleaning pipeline on raw data
cleaner = TextCleaner()
pipeline = [
    (cleaner.to_lower, "lower"),
    (cleaner.remove_diacritics, "diacritics"),
    (cleaner.normalize_nfkd, "nfkd"),
    (cleaner.strip, "strip"),
    (cleaner.remove_punctuation, "punctuation"),
    (cleaner.replace_hyphen_with_space, "hyphen"),
    (cleaner.expand_symbols, "symbol")
]
change_log = []
for fn, label in pipeline:
    logging.info(f"Starting pipeline step: {label}")
    df, counts = fn(df, subset_cols)
    change_log.append(counts)
    changes = ", ".join(f"{c}:{cnt}" for c,cnt in counts.items() if cnt)
    logging.info(f"Step {label} done. Changes: {changes or 'none'}")

# 3) Compute clusters
group_cols = ['country_standardized', 'factory_city_adm_name', 'owner_company_name', 'product_name']
complete_mask = df[group_cols].notna().all(axis=1)
df['cluster_num'] = np.nan 
df['cluster_id']  = '000000'
tmp = df.loc[complete_mask].copy()
tmp['cluster_num'] = tmp.groupby(group_cols).ngroup() + 1
sizes = tmp.groupby('cluster_num')['factory_city_adm_name'].transform('size')

tmp['cluster_id'] = (
    sizes.gt(1)                       # keep only clusters with ≥2 rows
    .mul(tmp['cluster_num'])          # multiply to keep the number or 0
    .astype(int)
    .astype(str)
    .str.zfill(6)                     # pad to six digits
)
df.loc[complete_mask, ['cluster_num', 'cluster_id']] = tmp[['cluster_num', 'cluster_id']]

# 4) Save output
output_cols = [col for col in [
    'factory_unique_id','factory_name','factory_city','factory_city_adm_name',
    'factory_country','country_standardized','country_iso2','country_not_found',
    'owner_company_unique_id','owner_company_name','product_name','factory_city_adm_code',
    'factory_city_adm_level','factory_city_latitude','factory_city_longitude','cluster_id'
] if col in df.columns]
output_file = "./storage/output/clean_output.xlsx"
logging.info(f"Saving output to {output_file}")
df[output_cols].to_excel(output_file, index=False)

# Final timing
t1_pipeline = time.time()
logging.info(f"Total pipeline time: {(t1_pipeline - t0_pipeline)/60:.2f} minutes")
