import pandas as pd
import uuid
from src.step_1 import TextCleaner
from src.company_mapping import map_to_canonical
from src.geonames_helpers import clean_city, clean_country, normalize_city_key
from src.step_2 import standardize_country
from src.load_geo_lookup import build_geo_lookup, get_geo_value
from src.set_adm_level import add_admin_group_key
from src.config import VEHICLES_IMPUTE, ZEV_PRODUCTION

def build_zev_og_clean_excel(
    input_excel_path: str = VEHICLES_IMPUTE,
    sheet_name: str = "production_to_impute",
    output_excel_path: str = ZEV_PRODUCTION,
    cutoff_date: str = "2025-05-31",
    article_id: str = "68d684fc1c2e9d8ed1487afa",
    to_excel: bool = True,
) -> pd.DataFrame:
    """
    Reads the 'production_to_impute' sheet, cleans/standardizes entities and geography,
    normalizes capacity, builds stable IDs, and writes a clean Excel. Returns the final DataFrame.
    """

    # --- Initiate helpers ---
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

    # --- Load minimal columns ---
    df = pd.read_excel(input_excel_path, sheet_name=sheet_name)
    df = df[[
        "company_name", "country", "city", "investment_type", "investment_status",
        "production_date_original", "production_date_current", "production_reported"
    ]].copy()

    # --- Company normalization ---
    df["inst_canon"] = df["company_name"].apply(cleaner.clean_string)
    df["inst_canon"] = df["inst_canon"].apply(map_to_canonical)

    # --- Geo normalization ---
    df["city_clean"] = df["city"].apply(clean_city)
    df["city_key"] = df["city_clean"].apply(normalize_city_key)
    df["country_clean"] = df["country"].apply(clean_country)
    df["iso2"] = df["country_clean"].apply(lambda x: standardize_country(x)[1])

    for col in ["adm1", "adm2", "adm3", "adm4", "lat", "lon"]:
        df[col] = df.apply(lambda r: get_geo_value(r, col, geo_lookup), axis=1)

    # --- Status / phase ---
    df["status"] = df["investment_status"].map(status_dictionary).fillna("unclear")
    df["phase"] = df["investment_type"].map(phase_dictionary).fillna("unclear")

    # --- Dates & cutoff ---
    for col in ["production_date_original", "production_date_current"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["date"] = df["production_date_current"].fillna(df["production_date_original"])
    cutoff = pd.Timestamp(cutoff_date)
    df = df[df["date"] <= cutoff]

    # --- Product tags ---
    df["product_lv1"] = "vehicle"
    df["product_lv2"] = "electric"

    # --- Capacity normalization ---
    # Divide by 0.67, round to nearest 10k, then adjust to nearest 20k
    df["capacity_normalized"] = (df["production_reported"] / 0.67).round(-4)
    df["capacity_normalized"] = (df["capacity_normalized"] / 20000).round() * 20000

    # --- Admin group key ---
    df = add_admin_group_key(df, out_col="admin_group_key")

    # --- Deterministic project_id / capacity_id ---
    NS = uuid.uuid5(uuid.NAMESPACE_URL, "bruegel/project-key/v1")

    df["project_key_tuple"] = list(zip(
        df["iso2"].astype(str),
        df["admin_group_key"].astype(str),
        df["inst_canon"].astype(str),
        df["product_lv1"].astype(str),
    ))
    df["project_key_str"] = df["project_key_tuple"].apply(lambda t: "|".join(map(str, t)))
    df["project_id"] = df["project_key_str"].apply(lambda s: str(uuid.uuid5(NS, s)))

    df["article_id"] = article_id
    df["capacity_id"] = df.apply(
        lambda row: f"{row['article_id']}_{row['project_id']}_{row['capacity_normalized']}",
        axis=1
    )

    # --- Output / return ---
    keep_cols = [
        "inst_canon", "city_clean", "city_key", "iso2",
        "capacity_normalized", "status", "phase", "date", "product_lv1", "product_lv2",
        "admin_group_key", "adm1", "adm2", "adm3", "adm4", "lat", "lon", "article_id",
        "project_id", "capacity_id", "project_key_str", "project_key_tuple"
    ]

    out_df = df[keep_cols].copy()
    if to_excel:
        out_df.to_excel(output_excel_path, index=False)
    return out_df

if __name__ == "__main__":
    _ = build_zev_og_clean_excel()