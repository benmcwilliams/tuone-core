import pandas as pd
import sys; sys.path.append("..")
from bson import ObjectId
from mongo_client import facilities_collection, articles_collection

# facility-level fields you want repeated on every phase row
FACILITY_FIELDS = [
    "project_id",
    "inst_canon",
    "iso2",
    "admin_group_key",
    #"lat",
    #"lon",
    "product_lv1",
    "product_lv2",
]


def build_phases_dataframe(query: dict | None = None) -> pd.DataFrame:
    """
    Build a flat dataframe with one row per phase.

    Each row contains:
      - facility-level info (FACILITY_FIELDS)
      - all keys from the phase object (status, capacity, investment, *_article_id, etc.)
    """
    if query is None:
        query = {}

    rows: list[dict] = []

    for doc in facilities_collection.find(query):
        phases = doc.get("phases") or []
        if not phases:
            continue  # skip facilities without phase summaries

        # base facility-level info (reused for each phase)
        base = {field: doc.get(field) for field in FACILITY_FIELDS}

        # optional: make product_lv2 more Excel-friendly (list -> comma-separated string)
        if isinstance(base.get("product_lv2"), (list, tuple, set)):
            base["product_lv2"] = ", ".join(map(str, base["product_lv2"]))

        for ph in phases:
            row = base.copy()
            # phase is already a flat dict: phase_num, status, capacity, *_article_id, etc.
            row.update(ph)
            rows.append(row)

    return pd.DataFrame(rows)


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
            # URL provenance columns
            "status_url",
            "capacity_url",
            "investment_url",
            "announced_url",
            "under_construction_url",
            "operational_url",
        ]
    )

    # keep only those that exist
    main_cols = [c for c in desired_order if c in df.columns]
    # any remaining columns (unexpected / future additions) at the end
    other_cols = [c for c in df.columns if c not in main_cols]

    return df[main_cols + other_cols]


def export_phases_to_excel(filepath: str, query: dict | None = None) -> pd.DataFrame:
    """
    Build the phase-level dataframe, attach URLs, drop article IDs,
    reorder columns cleanly, and write to an Excel file.
    Returns the dataframe for convenience.
    """
    df = build_phases_dataframe(query=query)
    
    df = df[df["product_lv1"].isin(["solar", "vehicle", "battery"])]
    #df = df[df["product_lv1"].isin(["vehicle", "battery"])]

    if "product_lv2" in df.columns:
        # treat NaN or empty/whitespace as blank
        is_blank = df["product_lv2"].isna() | (df["product_lv2"].astype(str).str.strip() == "")
        # rows where 'deployment' is NOT present (case-insensitive)
        not_deployment = ~df["product_lv2"].astype(str).str.contains("deployment", case=False, na=False)
        # keep only non-blank AND not containing 'deployment'
        df = df[~is_blank & not_deployment]


    df = attach_article_urls(df)

    # drop *_article_id columns, keep only URLs for export
    article_id_cols = [c for c in df.columns if c.endswith("_article_id")]
    if article_id_cols:
        df = df.drop(columns=article_id_cols)

    # tidy column order
    df = reorder_columns(df)

    df.to_excel(filepath, index=False)
    return df

if __name__ == "__main__":
    df = export_phases_to_excel("bruegel_investments.xlsx")

    n_phases = len(df)
    n_facilities = df["project_id"].nunique()

    print(f"Exported {n_phases} investment phases across {n_facilities} facilities.")