import os
import pandas as pd
import sys; sys.path.append("..")
from bson import ObjectId
from mongo_client import facilities_collection, articles_collection

bim_path = "storage/output/bruegel_investment_monitor.xlsx"
INCLUDE_LV1 = ["solar", "vehicle", "battery"]

# facility-level fields we want repeated on every phase row
FACILITY_FIELDS = [
    "project_id",
    "inst_canon",
    "iso2",
    "admin_group_key",
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

    # drop rows where all phase values are empty (we can drop this but this is typically noise that we have not bothered to validate out....)
    drop_cols = ["phase_capacity", "capacity", "phase_investment", "investment"]
    existing = [c for c in drop_cols if c in df.columns]

    if existing:
        df = df.dropna(subset=existing, how="all")
    
    df = df[df["product_lv1"].isin(INCLUDE_LV1)]

    if "product_lv2" in df.columns:
        # treat NaN or empty/whitespace as blank
        is_blank = df["product_lv2"].isna() | (df["product_lv2"].astype(str).str.strip() == "")
        # rows where 'deployment' is NOT present (case-insensitive)
        not_deployment = ~df["product_lv2"].astype(str).str.contains("deployment", case=False, na=False)
        # keep only non-blank AND not containing 'deployment'
        df = df[~is_blank & not_deployment]

    # collapse dates to monthly granularity (YYYY-MM)
    for col in ["announced_on", "under_construction_on", "operational_on"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m")

    df = attach_article_urls(df)

    # drop *_article_id columns, keep only URLs for export
    article_id_cols = [c for c in df.columns if c.endswith("_article_id")]
    if article_id_cols:
        df = df.drop(columns=article_id_cols)

    # tidy column order
    df = reorder_columns(df)

    # --- write each product_lv1 to its own sheet, preserving README ---
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Expected existing Excel file at: {filepath}")

    with pd.ExcelWriter(
        filepath,
        engine="openpyxl",
        mode="a",
        if_sheet_exists="replace",
    ) as writer:
        for pl1 in sorted(df["product_lv1"].unique()):
            sub = df[df["product_lv1"] == pl1].copy()

            # --- sort: owner, country, region (alphabetical), phase (numeric) ---
            if "phase" in sub.columns:
                # ensure numeric sort, fallback to NaN for non-numeric
                sub["phase"] = pd.to_numeric(sub["phase"], errors="coerce")

            sort_cols = [c for c in ["owner", "country", "region", "phase"] if c in sub.columns]
            sub = sub.sort_values(sort_cols, ascending=True)

            sub.to_excel(
                writer,
                sheet_name=pl1,
                index=False,
            )

    return df
    

if __name__ == "__main__":
    df = export_phases_to_excel(bim_path)

    n_phases = len(df)
    n_facilities = df["project_id"].nunique()

    total_investment = df["phase_investment"].sum(skipna=True)
    total_investment_mn = total_investment / 1e6

    print(
        f"Exported {n_phases} investment phases across {n_facilities} facilities "
        f"(total phase investment: {total_investment_mn:,.1f} million EUR)."
    )

    # Per-technology breakdown (one line per sheet/technology)
    for pl1 in sorted(df["product_lv1"].unique()):
        sub = df[df["product_lv1"] == pl1]
        n_phases_pl1 = len(sub)
        n_facilities_pl1 = sub["project_id"].nunique()

        inv_sum_pl1 = sub["phase_investment"].sum(skipna=True)
        inv_sum_pl1_mn = inv_sum_pl1 / 1e6

        print(
            f"  - {pl1}: {n_phases_pl1} phases across {n_facilities_pl1} facilities "
            f"({inv_sum_pl1_mn:,.1f} million EUR)."
        )
        