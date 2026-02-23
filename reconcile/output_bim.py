import os
import pandas as pd
import sys; sys.path.append("../")
from mongo_client import facilities_collection
from src.bim_helpers import ensure_parent_dir, make_excel_hyperlink, attach_article_urls, FACILITY_FIELDS
from src.bim_helpers import reorder_columns_gcim_long, reorder_columns
from src.assign_nuts import assign_nuts2_to_dataframe
from reconcile.phase_summary import parse_tract_stage
from currency_converter import CurrencyConverter
from datetime import date

_CCY = CurrencyConverter(
    fallback_on_missing_rate=True,
    fallback_on_wrong_date=True
)

bim_path = "storage/output/bruegel_investment_monitor.xlsx"
INCLUDE_LV1 = ["solar", "vehicle", "battery", "iron", "wind"]

def eur_to_usd(x):
    try:
        return _CCY.convert(x, "EUR", "USD", date=date(2023,7,1))
    except Exception:
        return None

EUR_USD_2023 = eur_to_usd(1)

def quarter_starts_inclusive_uc_exclusive_op(
    start: pd.Timestamp,
    end: pd.Timestamp,
    *,
    use_monthly_distribution: bool = False) -> list[pd.Period]:
    """
    Return quarters over which investment is distributed.

    If use_monthly_distribution = False (default):
        - snap UC and OP to quarter starts
        - include UC quarter
        - exclude OP quarter
        - split evenly across quarters

    If use_monthly_distribution = True:
        - distribute evenly across MONTHS (like plot/main.py)
        - then infer quarters from those months
        - quarters implicitly weighted by number of months
    """
    start = pd.to_datetime(start, errors="coerce")
    end = pd.to_datetime(end, errors="coerce")
    if pd.isna(start) or pd.isna(end):
        return []

    # -----------------------------
    # OPTION 1: match plot/main.py
    # -----------------------------
    if use_monthly_distribution:
        # snap to month starts
        uc_m = pd.Timestamp(start.year, start.month, 1)
        op_m = pd.Timestamp(end.year, end.month, 1)

        if op_m <= uc_m:
            return [uc_m.to_period("Q")]

        months = pd.date_range(
            start=uc_m,
            end=op_m,
            freq="MS",
            inclusive="left"
        )

        # map months → quarters (duplicates allowed upstream if needed)
        return sorted({m.to_period("Q") for m in months})

    # --------------------------------
    # OPTION 2: current quarterly logic
    # --------------------------------
    start_q = start.to_period("Q").to_timestamp(how="start")
    end_q   = end.to_period("Q").to_timestamp(how="start")

    if end_q <= start_q:
        return [start_q.to_period("Q")]

    qs = pd.date_range(
        start=start_q,
        end=end_q,
        freq="QS",
        inclusive="left"
    )

    return [q.to_period("Q") for q in qs]

def quarter_starts_inclusive_uc_exclusive_op(start: pd.Timestamp,
                                             end: pd.Timestamp) -> list[pd.Period]:
    """
    Quarterly analogue of month_starts_inclusive_uc_exclusive_op.

    Semantics:
    - include UC quarter
    - exclude OP quarter
    - interval is [UC, OP)
    """
    start = pd.to_datetime(start, errors="coerce")
    end = pd.to_datetime(end, errors="coerce")
    if pd.isna(start) or pd.isna(end):
        return []

    # snap both dates to quarter starts
    start_q = start.to_period("Q").to_timestamp(how="start")
    end_q   = end.to_period("Q").to_timestamp(how="start")

    if end_q <= start_q:
        return [start_q.to_period("Q")]

    qs = pd.date_range(
        start=start_q,
        end=end_q,
        freq="QS",
        inclusive="left"   # identical to monthly logic
    )

    return [q.to_period("Q") for q in qs]

def build_gcim_long(df: pd.DataFrame) -> pd.DataFrame:
    """
    Long format:
    - one row per (phase × quarter)
    - ONLY keep rows where both under_construction_on and operational_on exist
    - distribute phase_investment evenly across the inclusive quarter span
    - no fallbacks, no reversed-date guards
    - add investment_distribution = number of quarters receiving the split
    """
    req_cols = ["under_construction_on", "operational_on", "phase_investment"]
    missing = [c for c in req_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for gcim_long: {missing}")

    dfx = df.copy()

    # Ensure datetimes (rows that can't be parsed become NaT and are excluded)
    dfx["under_construction_on"] = pd.to_datetime(dfx["under_construction_on"], errors="coerce")
    dfx["operational_on"] = pd.to_datetime(dfx["operational_on"], errors="coerce")

    # Keep ONLY rows with both dates present which are under construction or operational
    dfx = dfx[dfx["under_construction_on"].notna() & dfx["operational_on"].notna()].copy()
    dfx = dfx[dfx["status"].isin(["under construction", "operational"])]

    out_rows: list[dict] = []

    for _, r in dfx.iterrows():
        start = r["under_construction_on"]
        end = r["operational_on"]

        qs = quarter_starts_inclusive_uc_exclusive_op(start, end)  # may be empty if end < start
        n = len(qs)
        if n == 0:
            continue  # distribute over zero quarters => no output rows

        inv = r["phase_investment"]
        per_q = float(inv) / n

        base = r.to_dict()
        #base["investment_distribution"] = n  # number of quarters receiving a slice

        for q in qs:
            row = base.copy()
            row["quarters"] = str(q)           # e.g. "2024Q1"
            row["investment_distribution_eur"] = per_q       # distributed amount for this quarter
            out_rows.append(row)

    out_df = pd.DataFrame(out_rows)
    out_df["investment_distribution"] = out_df["investment_distribution_eur"] * EUR_USD_2023

    return out_df

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
        if isinstance(base.get("product_lv3"), (list, tuple, set)):
            base["product_lv3"] = ", ".join(map(str, base["product_lv3"]))

        for ph in phases:
            row = base.copy() # phase is already a flat dict: phase_num, status, capacity, *_article_id, etc.
            row.update(ph) # this add new keys to the row, but also updates existing keys. Meaning it will overwrite facility level product_lv2.

            # Extract integer stage from phase_num (handles both "A.1" → 1 and legacy 1 → 1)
            if "phase_num" in row and row["phase_num"] is not None:
                _, stage = parse_tract_stage(row["phase_num"])
                if stage is not None:
                    row["phase_num"] = stage

            # Convert phase-level product_lv2/product_lv3 from list to comma-separated string
            if isinstance(row.get("product_lv2"), (list, tuple, set)):
                row["product_lv2"] = ", ".join(map(str, row["product_lv2"]))
            if isinstance(row.get("product_lv3"), (list, tuple, set)):
                row["product_lv3"] = ", ".join(map(str, row["product_lv3"]))
            rows.append(row)

    return pd.DataFrame(rows)

def export_phases_to_excel(filepath: str, query: dict | None = None) -> pd.DataFrame:
    """
    Build the phase-level dataframe, attach URLs, drop article IDs,
    reorder columns cleanly, and write to an Excel file.
    Returns the dataframe for convenience.
    """
    df = build_phases_dataframe(query=query)

    # Assign NUTS-2 regions based on lat/lon
    df = assign_nuts2_to_dataframe(df, lat_col="lat", lon_col="lon")

    # drop rows where all phase values are empty (we can drop this but this is typically noise that we have not bothered to validate out....)
    drop_cols = ["phase_capacity", "capacity", "phase_investment", "investment"]
    existing = [c for c in drop_cols if c in df.columns]
    if existing:
        # Drop rows with no capacity and no investment only for non-wind; keep all wind phases.
        all_missing = df[existing].isna().all(axis=1)
        is_wind = df["product_lv1"] == "wind"
        df = df[is_wind | ~all_missing]
    
    # limit to our current product selection 
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

    # replace URL strings with Excel hyperlinks labelled "source"
    url_cols = [c for c in df.columns if c.endswith("_url")]
    for col in url_cols:
        df[col] = df[col].apply(make_excel_hyperlink)

    # drop *_article_id columns, keep only URLs for export
    article_id_cols = [c for c in df.columns if c.endswith("_article_id")]
    if article_id_cols:
        df = df.drop(columns=article_id_cols)

    # --- unwrap comments dict: keep only the text (not to confuse externals) ---
    if "comments" in df.columns:
        df["comments"] = df["comments"].apply(
            lambda x: next(iter(x.values())) if isinstance(x, dict) and x else x
        )

    # tidy column order
    df = reorder_columns(df)

    # --- ensure output path + workbook exist ---
    ensure_parent_dir(filepath)

    # if workbook does not exist yet, create a minimal one so mode="a" works
    if not os.path.exists(filepath):
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            pd.DataFrame({"README": ["auto-created"]}).to_excel(
                writer, sheet_name="README", index=False
            )

    # --- write each product_lv1 to its own sheet, preserving README ---
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

        # output gcim long version
        gcim_long = build_gcim_long(df)

        q_min = pd.Period("2017Q1", freq="Q")
        q_max = pd.Period("2025Q3", freq="Q")

        gcim_long = gcim_long[
            gcim_long["quarters"].apply(lambda x: q_min <= pd.Period(x, freq="Q") <= q_max)
        ]

        gcim_long = reorder_columns_gcim_long(gcim_long)
        gcim_long.to_excel(
            writer,
            sheet_name="gcim_long",
            index=False,
        )

    return df
 

if __name__ == "__main__":

    # main export
    df = export_phases_to_excel(bim_path)

    # descriptive statistics
    n_phases = len(df)
    n_facilities = df["project_id"].nunique()

    total_investment = df["phase_investment"].sum(skipna=True)
    total_investment_mn = total_investment / 1e6

    print(
        f"Exported {n_phases} investment phases across {n_facilities} facilities "
        f"(total phase investment: {total_investment_mn:,.1f} million EUR)."
    )

    # per-technology breakdown (one line per sheet/technology)
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
        