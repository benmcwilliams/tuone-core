import os
import pandas as pd
import re
import sys; sys.path.append("../")
from mongo_client import facilities_collection
from src.bim_helpers import ensure_parent_dir, make_excel_hyperlink, attach_article_urls, FACILITY_FIELDS
from src.bim_helpers import reorder_columns_gcim_long, reorder_columns
from src.assign_nuts import assign_nuts2_to_dataframe
from reconcile.phase_summary import parse_tract_stage
from currency_converter import CurrencyConverter
from datetime import date
from src.config import BRUEGEL_IM

_CCY = CurrencyConverter(
    fallback_on_missing_rate=True,
    fallback_on_wrong_date=True
)

bim_path = BRUEGEL_IM
INCLUDE_LV1 = ["solar", "vehicle", "battery", "iron", "wind"]
EXCLUDE_LV2 = ["deployment", "hub", "monopile"]
MIN_ANNOUNCED_YEAR = 2016

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
        lv2 = df["product_lv2"].astype(str).str.strip()
        is_blank = df["product_lv2"].isna() | (lv2 == "")
        # exclude rows where product_lv2 contains any EXCLUDE_LV2 term (case-insensitive)
        exclude_terms = [str(v).strip() for v in EXCLUDE_LV2 if str(v).strip()]
        if exclude_terms:
            pattern = "|".join(map(re.escape, exclude_terms))
            is_excluded = lv2.str.contains(pattern, case=False, na=False)
        else:
            is_excluded = pd.Series(False, index=df.index)
        # keep only non-blank AND not excluded
        df = df[~is_blank & ~is_excluded]

    if "announced_on" in df.columns:
        announced_dates = pd.to_datetime(df["announced_on"], errors="coerce")
        min_announced_date = pd.Timestamp(MIN_ANNOUNCED_YEAR, 1, 1)
        df = df[announced_dates >= min_announced_date]

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

def write_country_status_investment_report(df: pd.DataFrame, output_path: str) -> None:
    """
    Write a fixed-width text report with country on rows and status on columns.
    Values are summed phase investment in million EUR.
    """
    required = {"country", "status", "phase_investment"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for country-status report: {sorted(missing)}")

    country_clean = (
        df["country"]
        .fillna("unknown")
        .astype(str)
        .str.strip()
        .replace("", "unknown")
    )
    status_clean = (
        df["status"]
        .fillna("unknown")
        .astype(str)
        .str.strip()
        .replace("", "unknown")
    )
    investment_clean = pd.to_numeric(df["phase_investment"], errors="coerce").fillna(0.0)

    report_df = pd.DataFrame(
        {
            "country": country_clean,
            "status": status_clean,
            "phase_investment": investment_clean,
        }
    )

    pivot = report_df.pivot_table(
        index="country",
        columns="status",
        values="phase_investment",
        aggfunc="sum",
        fill_value=0.0,
        margins=True,
        margins_name="TOTAL",
    )

    # Sort countries/statuses alphabetically, keep TOTAL at the end.
    row_order = sorted([r for r in pivot.index if r != "TOTAL"]) + ["TOTAL"]
    col_order = sorted([c for c in pivot.columns if c != "TOTAL"]) + ["TOTAL"]
    pivot = pivot.loc[row_order, col_order]
    pivot_mn = pivot / 1e6

    ensure_parent_dir(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("Country x Status investment report\n")
        f.write("Units: million EUR (sum of phase_investment)\n\n")
        f.write(pivot_mn.to_string(float_format=lambda x: f"{x:,.1f}"))
        f.write("\n")

def write_product_lv1_status_investment_report(df: pd.DataFrame, output_path: str) -> None:
    """
    Write a fixed-width text report with product_lv1 on rows and status on columns.
    Values are summed phase investment in million EUR.
    """
    required = {"product_lv1", "status", "phase_investment"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for product_lv1-status report: {sorted(missing)}")

    product_lv1_clean = (
        df["product_lv1"]
        .fillna("unknown")
        .astype(str)
        .str.strip()
        .replace("", "unknown")
    )
    status_clean = (
        df["status"]
        .fillna("unknown")
        .astype(str)
        .str.strip()
        .replace("", "unknown")
    )
    investment_clean = pd.to_numeric(df["phase_investment"], errors="coerce").fillna(0.0)

    report_df = pd.DataFrame(
        {
            "product_lv1": product_lv1_clean,
            "status": status_clean,
            "phase_investment": investment_clean,
        }
    )

    pivot = report_df.pivot_table(
        index="product_lv1",
        columns="status",
        values="phase_investment",
        aggfunc="sum",
        fill_value=0.0,
        margins=True,
        margins_name="TOTAL",
    )

    # Sort product_lv1/statuses alphabetically, keep TOTAL at the end.
    row_order = sorted([r for r in pivot.index if r != "TOTAL"]) + ["TOTAL"]
    col_order = sorted([c for c in pivot.columns if c != "TOTAL"]) + ["TOTAL"]
    pivot = pivot.loc[row_order, col_order]
    pivot_mn = pivot / 1e6

    ensure_parent_dir(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("Product_lv1 x Status investment report\n")
        f.write("Units: million EUR (sum of phase_investment)\n\n")
        f.write(pivot_mn.to_string(float_format=lambda x: f"{x:,.1f}"))
        f.write("\n")
 

if __name__ == "__main__":

    # main export
    df = export_phases_to_excel(bim_path)
    country_status_report_path = f"{os.path.splitext(bim_path)[0]}_country_status_investment.txt"
    write_country_status_investment_report(df, country_status_report_path)
    product_lv1_status_report_path = f"{os.path.splitext(bim_path)[0]}_product_lv1_status_investment.txt"
    write_product_lv1_status_investment_report(df, product_lv1_status_report_path)

    # descriptive statistics
    n_phases = len(df)
    n_facilities = df["project_id"].nunique()

    total_investment = df["phase_investment"].sum(skipna=True)
    total_investment_mn = total_investment / 1e6

    print(
        f"Exported {n_phases} investment phases across {n_facilities} facilities "
        f"(total phase investment: {total_investment_mn:,.1f} million EUR)."
    )
    print(f"Country-status investment report: {country_status_report_path}")
    print(f"Product_lv1-status investment report: {product_lv1_status_report_path}")

    # status-level investment breakdown
    if "status" in df.columns:
        status_labels = (
            df["status"]
            .fillna("unknown")
            .astype(str)
            .str.strip()
            .replace("", "unknown")
        )
        status_summary = (
            df.assign(status_clean=status_labels)
            .groupby("status_clean", dropna=False)["phase_investment"]
            .sum()
            .sort_values(ascending=False)
        )
        status_counts = status_labels.value_counts(dropna=False)

        print("Status breakdown:")
        for status, inv_sum in status_summary.items():
            inv_sum_mn = inv_sum / 1e6
            n_status = int(status_counts.get(status, 0))
            pct_total = (inv_sum / total_investment * 100) if total_investment else 0.0
            print(
                f"  - {status}: {n_status} phases "
                f"({inv_sum_mn:,.1f} million EUR, {pct_total:.1f}%)."
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
        