import os
import sys; sys.path.append("..")
from mongo_client import facilities_collection
import pandas as pd

ELIGIBLE = {"under construction", "operational"}

def _safe_ts(d):
    try: return pd.to_datetime(d)
    except Exception: return pd.NaT

def _month_starts_inclusive_uc_exclusive_op(uc_str, op_str):
    uc, op = _safe_ts(uc_str), _safe_ts(op_str)
    if pd.isna(uc) or pd.isna(op): return []
    uc = pd.Timestamp(uc.year, uc.month, 1)
    op = pd.Timestamp(op.year, op.month, 1)
    if op <= uc: return [uc]
    return list(pd.date_range(start=uc, end=op, freq="MS", inclusive="left"))

def load_investment_timeseries(group_fields=["product_lv1"], freq="Q",
                               start=None, end=None,
                               product_lv1_filter=None,
                               flatten_columns=True, sep=" | ") -> pd.DataFrame:
    """
    Returns a pivoted time series of ongoing investment.
    - group_fields: list of doc-level fields for columns (e.g., ["product_lv1"], ["iso2"], ["iso2","inst_canon"])
    - freq: "M" (monthly, MS) or quarterly aliases like "QE-DEC" (calendar quarters).
            Also supports "QE-MAR"/"QE-JUN"/"QE-SEP" for fiscal anchors.
    - start/end: inclusive bounds like "2021-01"
    - product_lv1_filter: list[str] to filter facilities by product_lv1 (e.g., ["battery"])
    - flatten_columns: join MultiIndex columns for Excel-friendly output
    """
    proj = {f: 1 for f in set(group_fields) | {"phases", "product_lv1"}}
    query = {"phases": {"$exists": True, "$ne": []}}
    if product_lv1_filter:
        query["product_lv1"] = {"$in": product_lv1_filter}

    cursor = facilities_collection.find(query, proj)

    rows = []
    for doc in cursor:
        group_vals = {f: doc.get(f) for f in group_fields}
        for ph in doc.get("phases", []):
            st, inv, uc, op = ph.get("status"), ph.get("phase_investment"), ph.get("under_construction_on"), ph.get("operational_on")
            if st not in ELIGIBLE or inv in (None, 0) or not (uc and op):
                continue
            months = _month_starts_inclusive_uc_exclusive_op(uc, op)
            if not months: continue
            monthly_amount = float(inv) / max(1, len(months))
            for m in months:
                row = {"month": m, "spend_eur": monthly_amount}
                row.update(group_vals)
                rows.append(row)

    if not rows:
        return pd.DataFrame(index=pd.to_datetime([], errors="coerce"))

    df = pd.DataFrame(rows)
    df["month"] = pd.to_datetime(df["month"]).dt.to_period("M").dt.to_timestamp()

    if start is not None:
        df = df[df["month"] >= pd.to_datetime(start).to_period("M").to_timestamp()]
    if end is not None:
        df = df[df["month"] <= pd.to_datetime(end).to_period("M").to_timestamp()]

    gb = df.groupby(["month"] + group_fields, as_index=False)["spend_eur"].sum()
    out = (gb.pivot(index="month", columns=group_fields, values="spend_eur")
             .fillna(0.0)
             .sort_index())

    # ---- Explicit resampling to avoid FutureWarning ("Q" -> use "QE-DEC") ----
    if freq:
        f = freq.upper()
        if f in {"Q", "QE", "Q-DEC", "QE-DEC"}:
            out = out.resample("QE-DEC").sum()  # calendar quarters (Mar/Jun/Sep/Dec ends)
            out.index.name = "quarter"
        elif f in {"M", "MS"}:
            out = out.resample("MS").sum()
            out.index.name = "month"
        else:
            # Allow custom fiscal quarter ends: "QE-MAR", "QE-JUN", "QE-SEP", etc.
            out = out.resample(f).sum()
            out.index.name = "period"
    else:
        out.index.name = "period"

    if flatten_columns and isinstance(out.columns, pd.MultiIndex):
        out.columns = [sep.join("" if v is None else str(v) for v in tup).strip() for tup in out.columns]
    return out

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path

if __name__ == "__main__":
    OUT_DIR = ensure_dir("storage/output/ongoing")

    # ---------- TOTAL (no product filter), quarterly by technology ----------
    total_q = load_investment_timeseries(
        group_fields=["product_lv1"], freq="QE-DEC", start="2021-01", end="2025-12"
    )
    total_q.to_excel(os.path.join(OUT_DIR, "ongoing_total_q.xlsx"))

    # ---------- FILTERED: battery ----------
    tech_filters = ["battery"]

    # (a) quarterly by technology (battery only)
    battery_q = load_investment_timeseries(
        group_fields=["product_lv1"], freq="QE-DEC", start="2021-01", end="2025-12",
        product_lv1_filter=tech_filters
    )
    battery_q.to_excel(os.path.join(OUT_DIR, "ongoing_battery_q.xlsx"))

    # (b) quarterly by iso2 (battery only)
    battery_by_iso2_q = load_investment_timeseries(
        group_fields=["iso2"], freq="QE-DEC", start="2021-01", end="2025-12",
        product_lv1_filter=tech_filters
    )
    battery_by_iso2_q.to_excel(os.path.join(OUT_DIR, "ongoing_battery_by_iso2_q.xlsx"))

    # (c) quarterly by iso2 + inst_canon (battery only)
    battery_by_iso2_inst_q = load_investment_timeseries(
        group_fields=["iso2", "inst_canon"], freq="QE-DEC", start="2021-01", end="2025-12",
        product_lv1_filter=tech_filters
    )
    battery_by_iso2_inst_q.to_excel(os.path.join(OUT_DIR, "ongoing_battery_by_iso2_inst_q.xlsx"))

    # (d) quarterly by inst_canon (battery only)
    battery_by_iso2_inst_q = load_investment_timeseries(
        group_fields=["inst_canon"], freq="QE-DEC", start="2021-01", end="2025-12",
        product_lv1_filter=tech_filters
    )
    battery_by_iso2_inst_q.to_excel(os.path.join(OUT_DIR, "ongoing_battery_by_inst_q.xlsx"))