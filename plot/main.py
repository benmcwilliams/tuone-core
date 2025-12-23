#### CODE ONLY BLOCKS DEPLOYMENT 
#### SHOULD INSTEAD PASS A DICTIONARY OF PRODUCT_LV2 per PRODUCT_LV1

import os
import sys; sys.path.append("..")
from mongo_client import facilities_collection
import pandas as pd
import matplotlib.pyplot as plt

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

def _quarter_starts_inclusive_uc_exclusive_op(uc_str, op_str):
    uc, op = _safe_ts(uc_str), _safe_ts(op_str)
    if pd.isna(uc) or pd.isna(op): 
        return []
    start_q = uc.to_period("Q").to_timestamp(how="start")
    end_q   = op.to_period("Q").to_timestamp(how="start")
    if end_q <= start_q:
        return [start_q]
    return list(pd.date_range(start=start_q, end=end_q, freq="QS", inclusive="left"))

def load_investment_timeseries(group_fields=["product_lv1"], freq="Q",
                               start=None, end=None,
                               product_lv1_filter=None,
                               use_quarter_snapping: bool = False,
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
    proj = {f: 1 for f in set(group_fields) | {"phases", "product_lv1", "product_lv2"}}
    query = {"phases": {"$exists": True, "$ne": []}}
    
    if product_lv1_filter:
        query["product_lv1"] = {"$in": product_lv1_filter}

    cursor = facilities_collection.find(query, proj)

    rows = []
    for doc in cursor:
        group_vals = {f: doc.get(f) for f in group_fields}

        # --- exclude deployment (mirror BIM export logic) ---
        pl2 = doc.get("product_lv2")
        if isinstance(pl2, (list, tuple, set)):
            pl2 = ", ".join(map(str, pl2))
        pl2 = "" if pl2 is None else str(pl2).strip()

        if not pl2 or "deployment" in pl2.lower():
            continue
        # ---------------------------------------------------

        for ph in doc.get("phases", []):
            st, inv, uc, op = ph.get("status"), ph.get("phase_investment"), ph.get("under_construction_on"), ph.get("operational_on")
            if st not in ELIGIBLE or inv in (None, 0) or not (uc and op):
                continue
            if use_quarter_snapping:
                periods = _quarter_starts_inclusive_uc_exclusive_op(uc, op)
                if not periods: 
                    continue
                per_amount = float(inv) / max(1, len(periods))
                for p in periods:
                    row = {"month": p, "spend_eur": per_amount}  # keep key name "month" to minimize downstream changes
                    row.update(group_vals)
                    rows.append(row)
            else:
                months = _month_starts_inclusive_uc_exclusive_op(uc, op)
                if not months: 
                    continue
                per_amount = float(inv) / max(1, len(months))
                for m in months:
                    row = {"month": m, "spend_eur": per_amount}
                    row.update(group_vals)
                    rows.append(row)
    if not rows:
        return pd.DataFrame(index=pd.to_datetime([], errors="coerce"))

    df = pd.DataFrame(rows)
    df["month"] = pd.to_datetime(df["month"])
    if not use_quarter_snapping:
        df["month"] = df["month"].dt.to_period("M").dt.to_timestamp()

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

def get_country_timeseries(freq="QE-DEC", start=None, end=None, product_lv1_filter=None):
    """
    Returns a tidy dataframe with columns: period, iso2, spend_eur.
    Detects whether index is 'month', 'quarter', or 'period'.
    """
    df = load_investment_timeseries(
        group_fields=["iso2"],
        freq=freq,
        start=start,
        end=end,
        product_lv1_filter=product_lv1_filter,
        flatten_columns=False
    )
    if df.empty:
        return pd.DataFrame(columns=["period", "iso2", "spend_eur"])

    # Detect index name automatically (month/quarter/period)
    idx_name = df.index.name or "period"

    # Convert wide pivot → long
    df = df.reset_index().melt(id_vars=idx_name, var_name="iso2", value_name="spend_eur")
    df.rename(columns={idx_name: "period"}, inplace=True)

    # Add an overall "TOTAL" series (sum of all countries per period)
    total = df.groupby("period", as_index=False)["spend_eur"].sum()
    total["iso2"] = "TOTAL"
    df = pd.concat([df, total], ignore_index=True)

    return df

def plot_country_investments(df, countries, out_path, freq_label="Quarterly"):
    """
    Plots up to six countries in a 2x3 subplot grid.
    """
    # keep only selected
    df = df[df["iso2"].isin(countries)]
    if df.empty:
        print("No data found for selected countries.")
        return

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharex=True)
    axes = axes.flatten()

    for i, iso in enumerate(countries):
        ax = axes[i]
        sub = df[df["iso2"] == iso]
        if sub.empty:
            ax.set_visible(False)
            continue
        ax.plot(sub["period"], sub["spend_eur"] / 1e6, lw=2)
        ax.set_title(f"{iso}", fontsize=12)
        ax.set_ylabel("€ million")
        ax.grid(True, alpha=0.3)

    fig.suptitle(f"{freq_label} battery and electric vehicle investment spending by country", fontsize=14, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Saved figure → {out_path}")

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path

if __name__ == "__main__":
    OUT_DIR = ensure_dir("storage/output/ongoing")
    start = '2017-01'
    end = '2025-09'

    # ---------- TOTAL (no product filter), quarterly by technology ----------
    total_q = load_investment_timeseries(
        group_fields=["product_lv1"], freq="QE-DEC", start=start, end=end, use_quarter_snapping=True
    )
    total_q.to_excel(os.path.join(OUT_DIR, "ongoing_total_q.xlsx"))

    # ---------- FILTERED: battery ----------
    tech_filters = ["battery","vehicle"]

    # (a) quarterly by technology (battery only)
    tech_q = load_investment_timeseries(
        group_fields=["product_lv1"], freq="QE-DEC", start=start, end=end,
        product_lv1_filter=tech_filters
    )
    tech_q.to_excel(os.path.join(OUT_DIR, "ongoing_tech_filter_q.xlsx"))

    # (b) quarterly by iso2 (battery only)
    tech_by_iso2_q = load_investment_timeseries(
        group_fields=["iso2"], freq="QE-DEC", start=start, end=end,
        product_lv1_filter=tech_filters
    )
    tech_by_iso2_q.to_excel(os.path.join(OUT_DIR, "ongoing_tech_filter_by_iso2_q.xlsx"))

    # (c) quarterly by iso2 + inst_canon (battery only)
    tech_by_iso2_inst_q = load_investment_timeseries(
        group_fields=["iso2", "inst_canon"], freq="QE-DEC", start=start, end=end,
        product_lv1_filter=tech_filters
    )
    tech_by_iso2_inst_q.to_excel(os.path.join(OUT_DIR, "tech_by_iso2_inst_q.xlsx"))

    # ---------- FIGURE: 6-country view ----------
    selected_countries = ["TOTAL", "DE", "FR", "HU", "ES", "SE"]  # edit freely
    df_countries = get_country_timeseries(
        freq="QE-DEC",
        start=start,
        end=end,
        product_lv1_filter=tech_filters
    )
    fig_path = os.path.join(OUT_DIR, "ongoing_6country_q.png")
    plot_country_investments(df_countries, selected_countries, fig_path, freq_label="Quarterly")