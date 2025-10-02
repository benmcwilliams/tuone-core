import pandas as pd 
import uuid
from src.step_1 import TextCleaner
from src.company_mapping import map_to_canonical
from src.geonames_helpers import clean_city, clean_country, normalize_city_key
from src.step_2 import standardize_country
from src.load_geo_lookup import build_geo_lookup, get_geo_value
from src.set_adm_level import add_admin_group_key

# drop any row that == Projected

# --- Initiate ---
cleaner = TextCleaner()
geo_lookup = build_geo_lookup()

status_dictionary = {
    'O': 'operational',
    'U': 'under construction',
    'A': 'announced',
    'C': 'cancelled',
    'R': 'cancelled',
    'I': 'announced'
}

phase_dictionary = {
    "Existing": "unclear",
    "Expansion": "expansion",
    "New": "greenfield",
    "Retrofit": "retrofit"
}

df = pd.read_excel("storage/input/vehicles_impute.xlsx", sheet_name="production_to_impute")

df = df[["company_name", "country", "city", "investment_type", "investment_status",
         "production_date_original", "production_date_current", "production_reported"]].copy()

# --- Pre-processing ---

# normalise company name to inst_canon & apply any manual mapping
df["inst_canon"] = df["company_name"].apply(cleaner.clean_string)
df['inst_canon'] = df['inst_canon'].apply(map_to_canonical)

# normalise cities via geonames collection
df["city_clean"] = df["city"].apply(clean_city)
df["city_key"] = df["city_clean"].apply(normalize_city_key)
df["country_clean"] = df["country"].apply(clean_country)
df["iso2"] = df["country_clean"].apply(lambda x: standardize_country(x)[1])

for col in ["adm1", "adm2", "adm3", "adm4", "lat", "lon"]:
    df[col] = df.apply(lambda r: get_geo_value(r, col, geo_lookup), axis=1)

# clean data storage

df["status"] = df["investment_status"].map(status_dictionary).fillna("unclear")
df["phase"] = df["investment_type"].map(phase_dictionary).fillna("unclear")

date_cols = ["production_date_original", "production_date_current"]
for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors="coerce")
df["date"] = df["production_date_current"].fillna(df["production_date_original"])

# filter out any rows after May 2025
cutoff = pd.Timestamp("2025-05-31")
df = df[df["date"] <= cutoff]

df["product_lv1"] = "vehicle"
df["product_lv2"] = "electric"

# rather than renamining, divide production value by 0.67 and round to the nearest 20,000. 
# rather than renaming, divide production value by 0.67 and round to nearest 20,000
df["capacity_normalized"] = (
    df["production_reported"] / 0.67
).round(-4)   # rounds to nearest 10,000

# adjust to nearest 20,000 instead of 10,000
df["capacity_normalized"] = (df["capacity_normalized"] / 20000).round() * 20000

# --- apply Hash for merging ---

df = add_admin_group_key(df, out_col="admin_group_key")
df["adm1"] = df["admin_group_key"]  # main pipeline uses adm1 := admin_group_key (still hacky fix for Ross)

# --- owner_key: singleton tuple (identical string form to main pipeline) ---
df["owner_key"] = df["inst_canon"].apply(lambda x: (x,) if isinstance(x, str) and x.strip() else tuple())

# --- build deterministic project_id (same namespace, same key order, same stringification) ---
NS = uuid.uuid5(uuid.NAMESPACE_URL, "bruegel/project-key/v1")

df["project_key_tuple"] = list(zip(
    df["iso2"].astype(str),
    df["adm1"].astype(str),
    df["owner_key"].astype(str),
    df["product_lv1"].astype(str),
))

df["project_key_str"] = df["project_key_tuple"].apply(lambda t: "|".join(map(str, t)))
df["project_id"] = df["project_key_str"].apply(lambda s: str(uuid.uuid5(NS, s)))
df["article_id"] = "68d684fc1c2e9d8ed1487afa"
df["capacity_id"] = df.apply(
    lambda row: f"{row['article_id']}_{row['project_id']}_{row['capacity_normalized']}", 
    axis=1
)

# --- clean excel output ---

keep_cols = [
            "inst_canon", "city_clean", "city_key", "iso2",
             "capacity_normalized","status", "phase", "date", "product_lv1", "product_lv2",
             "admin_group_key","adm1", "adm2", "adm3", "adm4", "lat", "lon", "article_id",
             "project_id", "capacity_id", "project_key_str", "project_key_tuple"]

df[keep_cols].to_excel("storage/input/zev_og_clean.xlsx", index=False)


