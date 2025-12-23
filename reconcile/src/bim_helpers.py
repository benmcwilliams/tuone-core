import sys; sys.path.append("../..")
from bson import ObjectId
from pathlib import Path
import pandas as pd
from mongo_client import articles_collection

### CONFIG

# facility-level fields we want repeated on every phase row
FACILITY_FIELDS = [
    "project_id",
    "inst_canon",
    "iso2",
    "admin_group_key",
    "product_lv1",
    "product_lv2",
    "lat",
    "lon"
]

### UTILS

def make_excel_hyperlink(url):
    if pd.isna(url) or not isinstance(url, str) or not url.strip():
        return None
    return f'=HYPERLINK("{url}", "source")'

def ensure_parent_dir(filepath: str) -> None:
    Path(filepath).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

def attach_article_urls(df: pd.DataFrame) -> pd.DataFrame:
    """
    For every column that ends with '_article_id', look up the corresponding
    meta.url in articles_collection and create a parallel '..._url' column.
    """
    # find all article id columns
    article_id_cols = [c for c in df.columns if c.endswith("_article_id")]
    if not article_id_cols:
        return df

    # collect all unique IDs as strings
    ids: set[str] = set()
    for col in article_id_cols:
        ids.update(
            str(x)
            for x in df[col].dropna().unique()
            if isinstance(x, str) and x.strip()
        )

    if not ids:
        return df

    # convert to ObjectId list (filter out any invalid)
    obj_ids = []
    for s in ids:
        try:
            obj_ids.append(ObjectId(s))
        except Exception:
            # skip malformed ids
            continue

    if not obj_ids:
        return df

    # build mapping: hex(ObjectId) -> meta.url
    id_to_url: dict[str, str | None] = {}
    for doc in articles_collection.find(
        {"_id": {"$in": obj_ids}},
        {"meta.url": 1}
    ):
        url = doc.get("meta", {}).get("url")
        id_to_url[str(doc["_id"])] = url

    # add URL columns
    for col in article_id_cols:
        url_col = col.replace("_article_id", "_url")
        df[url_col] = df[col].map(lambda x: id_to_url.get(str(x)) if pd.notna(x) else None)

    return df

#### FORMATTING


def reorder_columns_gcim_long(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean column names + order for gcim_long export.
    Assumes df is already the renamed 'wide' df (owner/country/region/phase...).
    """

    rename_map = {
        "product_lv1": "technology",
        "region": "city",
        "lat": "latitude",
        "lon": "longitude",
        "owner": "company_name",
        "phase": "investment_type",
        "status": "investment_status",
        "announced_on": "announcement_date",
        "under_construction_on": "construction_start",
        "operational_on": "production_date",
        "product_lv2": "product_classification",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    desired_order = [
        "country",
        "region",
        "technology",
        "project_id",
        "city",
        "longitude",
        "latitude",
        "company_name",
        "investment_type",
        "investment_status",
        "announcement_date",
        "construction_start",
        "production_date",
        "quarters",
        "investment_distribution",
        "investment_distribution_eur",
        "product_classification",
    ]

    main_cols = [c for c in desired_order if c in df.columns]
    return df[main_cols]

def reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply a clean, custom column order for the Excel export.
    """
    # rename any columns as necessary
    rename_map = {
        "inst_canon": "owner",    
        "iso2": "country",         
        "admin_group_key": "region",
        "phase_num": "phase",
        "capacity": "capacity_cumulative",
        "investment": "investment_cumulative",
    }
    df = df.rename(columns=rename_map)

    # desired order "skeleton"
    desired_order = (
        [
            "owner",
            "country",
            "region",
            "product_lv1",
            "product_lv2",
            "phase",
            "status",
            "phase_capacity",
            "capacity_cumulative",
            "phase_investment",
            "investment_cumulative",
            "investment_was_imputed",
            "announced_on",
            "under_construction_on",
            "operational_on",
            "ann_date_imputed",
            "uc_date_imputed",
            "op_date_imputed",
            "comments",
            # URL provenance columns
            "status_url",
            "capacity_url",
            "investment_url",
            "announced_url",
            "under_construction_url",
            "operational_url",
            "project_id"
        ]
    )

    # keep only those that exist
    main_cols = [c for c in desired_order if c in df.columns]
    # any remaining columns (unexpected / future additions) at the end
    other_cols = [c for c in df.columns if c not in main_cols]

    return df[main_cols + other_cols]