# -*- coding: utf-8 -*-
import sys; sys.path.append("..")

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, List, Union

from mongo_client import facilities_collection
from src.config import CAPACITIES_PLOT

## to do, update script to read in phases and consider rather than only main
# -------------------------------------------------
# Load
# -------------------------------------------------
STATUS_ORDER = ["operational", "under construction", "announced"]
FIG_DIR = "storage/figures"
STATUS_COLORS = {
    "operational": "#8B0000",        # dark red
    "under construction": "#FFA07A", # light salmon (faded orange/red)
    "announced": "#7f7f7f",          # grey
}

def load_facility_df():
    pipeline = [
        {"$project": {
            "_id": 0,
            "owner": "$inst_canon",
            "iso2": 1, "adm1": 1,
            "product_lv1": 1, "product_lv2": 1,
            "status": "$main.status",
            "capacity": "$main.capacity",
            "investment":"$main.investment",
            "announced_on": "$main.announced_on",
            "under_construction_on": "$main.under_construction_on",
            "operational_on": "$main.operational_on"
        }}
    ]
    rows = list(facilities_collection.aggregate(pipeline))
    df = pd.DataFrame(rows)

    # ensure product_lv2 is a scalar (explode lists)
    df["product_lv2"] = df["product_lv2"].apply(
        lambda x: x if isinstance(x, list) else ([x] if x is not None else [pd.NA])
    )
    df = df.explode("product_lv2", ignore_index=True)

    # dates -> Period[Q] columns + validation prints
    date_cols = ["announced_on", "under_construction_on", "operational_on"]
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
            qcol = c + "_quarter"
            df[qcol] = df[c].dt.to_period("Q")  # keep as Period[Q] for natural chrono order

            # --- validation printouts ("printf") ---
            orig_notna = int(df[c].notna().sum())
            q_notna    = int(df[qcol].notna().sum())
            mismatches = df[c].notna() & df[qcol].isna()
            n_mismatch = int(mismatches.sum())
            uniq_quarters = df.loc[df[qcol].notna(), qcol].unique()

            print(f"[quarters] {c}: non-null dates={orig_notna}, non-null quarters={q_notna}, mismatches={n_mismatch}")
            if n_mismatch:
                print(df.loc[mismatches, [c, qcol]].head(5))
            # quick peek at unique quarters (first 10) in chrono order
            try:
                uniq_quarters_sorted = pd.PeriodIndex(uniq_quarters, freq='Q').sort_values()
                print(f"[quarters] {c}: sample quarters -> {[f'{p.year}-Q{p.quarter}' for p in uniq_quarters_sorted[:10]]}")
            except Exception:
                pass

    # coerce capacities if objects slipped in
    for c in ["capacity", "investment"]:
        if c in df.columns and df[c].dtype == "object":
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # optional export of the flat table (Period will export as strings like 2024Q1)
    output_cols = [
        "iso2","adm1","owner","product_lv1","product_lv2","status",
        "capacity","investment",
        "announced_on","announced_on_quarter",
        "under_construction_on","under_construction_on_quarter",
        "operational_on","operational_on_quarter",
    ]
    df.to_excel(CAPACITIES_PLOT, columns=[c for c in output_cols if c in df.columns], index=False)

    return df



# -------------------------------------------------
# Merge
# -------------------------------------------------
# OPTIONAL GLOBALS from your codebase (only used if stack_col == "status")
# - STATUS_ORDER: list[str]
# - STATUS_COLORS: dict[str, str]
import pandas as pd
from pathlib import Path
import pandas as pd

# Example DataFrame
df_owner = pd.DataFrame({
    "countryHQ": [
        'Italy', 'Switzerland', 'Spain', 'Germany', 'India', 'United States',
        'France', 'Japan', 'United Kingdom', 'Sweden', 'Netherlands', 'Ireland',
        'Hungary', 'Poland', 'Belgium', 'Luxembourg', 'China', 'Canada',
        'Slovakia', 'Denmark', 'Lithuania', 'Austria', 'Unknown', 'Czech Republic',
        'Romania', 'Croatia', 'Finland', 'Latvia', 'Israel', 'South Korea',
        'Portugal', 'Norway', 'Bulgaria', 'Estonia', 'Greece', 'Australia',
        'Singapore', 'Russia', 'Saudi Arabia', 'USA', 'Taiwan', 'Kenya', 'Ghana'
    ]
})

# Define EU countries
eu_countries = {
    'Austria','Belgium','Bulgaria','Croatia','Cyprus','Czech Republic','Denmark',
    'Estonia','Finland','France','Germany','Greece','Hungary','Ireland','Italy',
    'Latvia','Lithuania','Luxembourg','Malta','Netherlands','Poland','Portugal',
    'Romania','Slovakia','Slovenia','Spain','Sweden'
}

# Mapping function
def map_region(country):
    if country in eu_countries:
        return "EU"
    elif country in ["United States", "USA"]:
        return "US"
    elif country == "China":
        return "China"
    elif country == "Japan":
        return "Japan"
    elif country == "South Korea":
        return "South Korea"
    else:
        return "Other"



def _normalize_owner_key(s: pd.Series) -> pd.Series:
    # Robust normalization for joins
    return (
        s.astype(str)
         .str.strip()
         .str.replace(r"\s+", " ", regex=True)
         .str.lower()
    )

def merge_owner(df: pd.DataFrame, owner: pd.DataFrame) -> pd.DataFrame:
    print("\n[merge_owner] Initial shapes:")
    print(f"- df:    {df.shape}")
    print(f"- owner: {owner.shape}")

    print("\n[merge_owner] Initial columns:")
    print(f"- df.columns:    {list(df.columns)}")
    print(f"- owner.columns: {list(owner.columns)}")

    # Ensure df has an 'owner' column
    if "owner" not in df.columns:
        if "inst_canon" in df.columns:
            df = df.rename(columns={"inst_canon": "owner"})
            print("[merge_owner] Renamed df column 'inst_canon' -> 'owner'")
        else:
            print("[merge_owner][ERROR] No 'owner' or 'inst_canon' column in df. Aborting merge.")
            return df

    # Ensure owner has an 'owner' column
    if "owner" not in owner.columns:
        if "inst_canon" in owner.columns:
            owner = owner.rename(columns={"inst_canon": "owner"})
            print("[merge_owner] Renamed owner column 'inst_canon' -> 'owner'")
        else:
            print("[merge_owner][ERROR] No 'owner' or 'inst_canon' column in owner. Aborting merge.")
            return df

    # Normalize join key on both sides
    df["owner"] = _normalize_owner_key(df["owner"])
    owner["owner"] = _normalize_owner_key(owner["owner"])

    # Quick diagnostics on keys
    print("\n[merge_owner] Key diagnostics (after normalization):")
    print(f"- df['owner']:    nulls={df['owner'].isna().sum()}, unique={df['owner'].nunique()}")
    print(f"- owner['owner']: nulls={owner['owner'].isna().sum()}, unique={owner['owner'].nunique()}")

    overlap = set(df["owner"].dropna().unique()) & set(owner["owner"].dropna().unique())
    print(f"- overlap of keys: {len(overlap)}")

    # Optional: print a few example keys
    print(f"- sample df owners:    {df['owner'].dropna().unique()[:5]}")
    print(f"- sample owner owners: {owner['owner'].dropna().unique()[:5]}")

    # Do the merge with indicator to see what happened
    merged = df.merge(owner, on="owner", how="left", suffixes=("", "_owner"), indicator=True)

    print("\n[merge_owner] Merge indicator breakdown:")
    print(merged["_merge"].value_counts(dropna=False))

    # Show a few unmatched left keys
    left_only_keys = merged.loc[merged["_merge"] == "left_only", "owner"].dropna().unique()[:10]
    if len(left_only_keys):
        print(f"[merge_owner] Sample unmatched df.owner keys (up to 10): {left_only_keys}")
    

    # Drop the indicator column before returning (optional)
    merged = merged.drop(columns=["_merge"])

    print(f"\n[merge_owner] Final shape: {merged.shape}")
    return merged




# -------------------------------------------------
# Helpers
# -------------------------------------------------

def _dedup_seq(seq: List[str]) -> List[str]:
    seen = set()
    out = []
    for s in seq:
        if s not in seen:
            out.append(s); seen.add(s)
    return out

def _derive_index_by(cfg: Dict[str, Any], stack_col: str) -> List[str]:
    """
    Backward-compatible:
      - Prefer 'index_by' if present.
      - Else use 'group_by' (legacy), but drop stack_col if it's there.
      - Default to ['iso2', 'regionHQ'] minus stack_col.
    """
    if "index_by" in cfg:
        idx = list(cfg["index_by"])
    else:
        idx = list(cfg.get("group_by", ["iso2", "regionHQ"]))
    idx = [c for c in idx if c != stack_col]
    return _dedup_seq(idx)

def _stack_config_for_chart(batch_cfg: Dict[str, Any], chart_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve stack settings with precedence: chart-level > batch-level > defaults.
    Returns dict with keys: column, order (or None), colors (or None), legend_title (or None)
    """
    # batch-level defaults
    batch_stack = batch_cfg.get("stack", {})
    chart_stack = chart_spec.get("stack", {})

    stack_col = chart_stack.get("column", batch_stack.get("column", "status"))
    stack_order = chart_stack.get("order", batch_stack.get("order", None))
    stack_colors = chart_stack.get("colors", batch_stack.get("colors", None))
    legend_title = chart_stack.get("legend_title", batch_stack.get("legend_title", None))

    # convenience: if stacking on 'status' and no legend title provided
    if legend_title is None:
        legend_title = stack_col.capitalize()

    # if stacking on status and global STATUS_ORDER/COLORS exist, use as fallback
    if stack_col == "status":
        if stack_order is None:
            try:
                from __main__ import STATUS_ORDER as _STATUS_ORDER  # type: ignore
                stack_order = _STATUS_ORDER
            except Exception:
                pass
        if stack_colors is None:
            try:
                from __main__ import STATUS_COLORS as _STATUS_COLORS  # type: ignore
                stack_colors = _STATUS_COLORS
            except Exception:
                pass

    return {
        "column": stack_col,
        "order": stack_order,
        "colors": stack_colors,
        "legend_title": legend_title,
    }

# -------------------------------------------------
# Pivot (now flexible stack dimension)
# -------------------------------------------------
def plot_stacked_bar_flex(
    pivot: pd.DataFrame,
    *,
    title: str,
    outfile_png: str,
    plot_cfg: Dict[str, Any],
    index_label: str | None,
    stack_colors: Dict[str, str] | None,
    legend_title: str | None,
):
    if pivot.empty:
        print(f"[skip] No data to plot for: {title}")
        return

    if "total__" not in pivot.columns:
        pivot["total__"] = pivot.sum(axis=1, numeric_only=True)

    # ordering
    order_by = plot_cfg.get("order_by", "total_desc")
    if order_by == "total_desc":
        pivot = pivot.sort_values(by="total__", ascending=False)
    elif order_by == "total_asc":
        pivot = pivot.sort_values(by="total__", ascending=True)
    elif order_by == "index_asc":
        pivot = pivot.sort_index(ascending=True)
    elif order_by == "index_desc":
        pivot = pivot.sort_index(ascending=False)

    # top N (leave None to keep all quarters)
    top_n = plot_cfg.get("top_n")
    if isinstance(top_n, int) and top_n > 0:
        pivot = pivot.head(top_n)

    # stack columns (exclude helper)
    stack_cols = [c for c in pivot.columns if c != "total__"]

    # normalize
    normalize = bool(plot_cfg.get("normalize", False))
    if normalize:
        denom = pivot[stack_cols].sum(axis=1).replace(0, 1)
        pivot_plot = pivot[stack_cols].div(denom, axis=0)
        value_axis_label = "Share (100%)"
    else:
        pivot_plot = pivot[stack_cols]
        value_axis_label = plot_cfg.get("x_unit", "Value")

    # figure params
    figsize = tuple(plot_cfg.get("figsize", (10, 6)))
    dpi = int(plot_cfg.get("dpi", 300))
    os.makedirs(os.path.dirname(outfile_png), exist_ok=True)

    # colors
    color_kw = {}
    if stack_colors:
        color_kw["color"] = [stack_colors.get(c, "#cccccc") for c in pivot_plot.columns]

    # orientation
    orientation = plot_cfg.get("orientation", "hbar").lower()
    kind = "barh" if orientation == "hbar" else "bar"

    ax = pivot_plot.plot(kind=kind, stacked=True, figsize=figsize, **color_kw)

    # axis labels
    if orientation == "hbar":
        ax.set_xlabel(value_axis_label)
        ax.set_ylabel(index_label or "Index")
    else:
        ax.set_xlabel(index_label or "Index")
        ax.set_ylabel(value_axis_label)

    ax.set_title(title)

    # ---- Force ALL quarter ticks & pretty labels (YYYY-Qn) ----
    def _fmt_quarter_labels(idx):
        # idx can be PeriodIndex or anything; try to format as YYYY-Qn
        out = []
        for v in idx:
            try:
                p = v if isinstance(v, pd.Period) else pd.Period(str(v), freq="Q")
                out.append(f"{p.year}-Q{p.quarter}")
            except Exception:
                out.append(str(v))
        return out

    if isinstance(pivot_plot.index, pd.PeriodIndex) and (pivot_plot.index.freqstr or "").upper().startswith("Q"):
        labels = _fmt_quarter_labels(pivot_plot.index)
        if orientation == "vbar":
            ax.set_xticks(np.arange(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha="right")
        else:
            ax.set_yticks(np.arange(len(labels)))
            ax.set_yticklabels(labels)

    # legend
    if plot_cfg.get("legend_outside", True):
        ncol = int(plot_cfg.get("legend_ncol", 1))
        ax.legend(
            loc="center left",
            bbox_to_anchor=(1.0, 0.5),
            frameon=False,
            ncol=ncol,
            title=legend_title or "Legend"
        )
        plt.tight_layout(rect=[0, 0, 0.8, 1])
    else:
        leg = ax.legend(title=legend_title or "Legend")
        if leg:
            leg.set_frame_on(False)
        plt.tight_layout()

    # value labels at bar tip
    if plot_cfg.get("show_value_labels", True):
        if orientation == "hbar":
            for i, (idx, _) in enumerate(pivot_plot.iterrows()):
                total_val = 1.0 if normalize else pivot.loc[idx, "total__"]
                label = f"{total_val*100:.0f}%" if normalize else f"{total_val:,.0f}"
                ax.text(pivot_plot.loc[idx].sum(), i, f" {label}", va="center", fontsize=8)
        else:
            for i, idx in enumerate(pivot_plot.index):
                total_val = 1.0 if normalize else pivot.loc[idx, "total__"]
                label = f"{total_val*100:.0f}%" if normalize else f"{total_val:,.0f}"
                ax.text(i, pivot_plot.loc[idx].sum(), f"{label}", ha="center", va="bottom", fontsize=8)

    plt.savefig(outfile_png, dpi=dpi, bbox_inches="tight")
    plt.close()


# -------------------------------------------------
# Plot (uses flexible stack dimension)
# -------------------------------------------------

def build_pivot_flex(
    df: pd.DataFrame,
    lv1: str,
    lv2: str,
    *,
    value_col: str = "capacity",
    index_by: List[str] = ("iso2", "regionHQ"),
    stack_col: str = "status",
    stack_order: List[str] | None = None,
) -> pd.DataFrame:
    """
    Filters df on product_lv1/product_lv2 (optional), groups by index_by + stack_col,
    returns a wide pivot with stack_col values as columns and a 'total__' helper.
    """
    # ✅ Start from full data; filter only when not ALL/*/None
    sub = df.copy()

    if lv1 not in (None, "ALL", "*"):
        sub = sub[sub["product_lv1"] == lv1]
    if lv2 not in (None, "ALL", "*"):
        sub = sub[sub["product_lv2"] == lv2]

    if sub.empty:
        return pd.DataFrame()

    group_by = _dedup_seq(list(index_by) + [stack_col])

    grouped = (
        sub.groupby(group_by, dropna=False)[value_col]
           .sum(min_count=1, numeric_only=True)
           .reset_index()
    )

    pivot = (
        grouped.pivot_table(index=index_by, columns=stack_col, values=value_col, fill_value=0.0)
               .fillna(0.0)
    )

    # Keep declared stack order (if provided), then any leftovers
    if stack_order:
        leftovers = [c for c in pivot.columns if c not in stack_order]
        pivot = pivot.reindex(columns=list(stack_order) + leftovers, fill_value=0.0)

    # Expand continuous quarters if index is a Period[Q]
    if isinstance(pivot.index, pd.PeriodIndex) and getattr(pivot.index, "freqstr", "").upper().startswith("Q"):
        full = pd.period_range(pivot.index.min(), pivot.index.max(), freq="Q")
        pivot = pivot.reindex(full, fill_value=0.0)

    if "total__" not in pivot.columns:
        pivot["total__"] = pivot.sum(axis=1, numeric_only=True)

    return pivot

# -------------------------------------------------
# Batch runner (multi-metric, flexible stacking)
# -------------------------------------------------
def _apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """
    Supports:
      - Categorical: {"col": ["A","B"]} or {"col": "A"}
      - Numeric mins/maxes: {"capacity_min": 1000, "investment_max": 5e6}
      - Not-in lists: {"status_not": ["announced"]}
      - Regex contains: {"owner_regex": ".*sa.*"}  (case-insensitive)
      - Date mins/maxes: {"operational_on_min": "2021-01-01", "operational_on_max": "2024-12-31"}
    """
    sub = df.copy()

    for key, val in (filters or {}).items():
        if key.endswith("_min"):
            base = key[:-4]
            sub = sub[sub[base] >= val]
        elif key.endswith("_max"):
            base = key[:-4]
            sub = sub[sub[base] <= val]
        elif key.endswith("_not"):
            base = key[:-4]
            vals = val if isinstance(val, (list, tuple, set)) else [val]
            sub = sub[~sub[base].isin(vals)]
        elif key.endswith("_regex"):
            base = key[:-6]
            sub = sub[sub[base].astype(str).str.contains(val, case=False, regex=True, na=False)]
        else:
            # categorical include
            vals = val if isinstance(val, (list, tuple, set)) else [val]
            sub = sub[sub[key].isin(vals)]

    return sub

def _run_single_batch(df: pd.DataFrame, cfg: Dict[str, Any]) -> None:
    """
    One batch = one metric/output_dir/[index_by]/plot spec with many charts.
    Supports:
      - batch-level filters via cfg['filters']
      - chart-level filters via spec['filters'] (applied on top of batch filters)
      - flexible stack column via cfg['stack'] or chart['stack'].
    """
    # metric & axes labels
    value_col_default = cfg.get("value_col", "capacity")
    plot_cfg = cfg.get("plot", {})
    outdir_base = cfg.get("output_dir", "figs")
    os.makedirs(outdir_base, exist_ok=True)

    # apply batch-level filters ONCE to a base copy
    df_base = _apply_filters(df, cfg.get("filters", {}))

    for spec in cfg.get("charts", []):
        lv1 = spec["lv1"]; lv2 = spec["lv2"]; title = spec["title"]

        # optional chart-level filters layered on top
        df_use = _apply_filters(df_base, spec.get("filters", {}))

        # resolve stack (chart overrides batch)
        sconf = _stack_config_for_chart(cfg, spec)
        stack_col = sconf["column"]
        stack_order = sconf["order"]
        stack_colors = sconf["colors"]
        legend_title = sconf["legend_title"]

        # index_by (y-axis categories)
        index_by = _derive_index_by(cfg, stack_col)

        # per-chart override for value_col
        value_col = spec.get("value_col", value_col_default)

        # output path
        fname = spec["filename"]
        path = fname if os.path.isabs(fname) else os.path.join(outdir_base, fname)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # y-axis label
        index_label = (
            cfg.get("index_name_override")
            or cfg.get("index_label")
            or "/".join(index_by)
        )

        print(f"\n[batch:{cfg.get('name','default')}] {lv1}/{lv2} stack={stack_col} -> {path}")

        pivot = build_pivot_flex(
            df_use, lv1, lv2,
            value_col=value_col,
            index_by=index_by,
            stack_col=stack_col,
            stack_order=stack_order
        )
        if pivot.empty:
            print("[skip] empty subset")
            continue

        plot_stacked_bar_flex(
            pivot=pivot,
            title=title,
            outfile_png=path,
            plot_cfg=plot_cfg,
            index_label=index_label,
            stack_colors=stack_colors,
            legend_title=legend_title
        )

def output_plots_from_config(df: pd.DataFrame, config: Union[str, Dict[str, Any]]) -> None:
    """
    Entry point. Accepts dict config or path to JSON.
    Supports multiple batches via top-level 'batches'; else single-batch.
    """
    if isinstance(config, str):
        with open(config, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = config

    if "batches" in cfg and isinstance(cfg["batches"], list):
        for batch_cfg in cfg["batches"]:
            _run_single_batch(df, batch_cfg)
    else:
        _run_single_batch(df, cfg)

######----------------------------- Capacity vs demand---------
# Map product_lv2 -> product_lv1 key for demand lookup (fallback only)
LV2_TO_LV1 = {
    "module_pack": "battery",
    "ingot_wafer": "solar",
    "polysilicon": "solar",
    "electric": "vehicles",

}

def _mk_lv1_lv2(sr_lv1: pd.Series, sr_lv2: pd.Series) -> pd.Series:
    # robust: lowercase, strip, collapse spaces/underscores, handle NaNs
    a = sr_lv1.astype("string").str.strip().str.lower().fillna("unknown")
    b = sr_lv2.astype("string").str.strip().str.lower().fillna("unknown")
    return a + "_" + b

def plot_capacity_vs_demand_lv2(
    df: pd.DataFrame,
    *,
    demand: dict[str, float],
    outfile_png: str,
    include_lv2: list[str] = ("cell","module_pack","ingot_wafer","polysilicon","electric"),
    status_filter: list[str] = ("operational","under construction","announced"),
    normalize_to_demand: bool = True,
    title: str = "Capacity vs demand by product level 2",
    figsize=(11, 7),
    dpi: int = 300
):
    """
    Horizontal stacked bar by STATUS; one bar per (lv1_lv2).
    Demand is looked up from the parent lv1 (prefix before underscore).
    """
    sub = df[df["status"].isin(status_filter)].copy()

    # filter on lv2 as before (optional)
    sub = sub[sub["product_lv2"].isin(list(include_lv2))]

    # build combined y-axis key
    sub["lv1_lv2"] = _mk_lv1_lv2(sub["product_lv1"], sub["product_lv2"])

    # parent lv1: prefer actual col; fallback from lv2 map if missing
    sub["parent_lv1"] = sub["product_lv1"].astype("string")
    mask_na = sub["parent_lv1"].isna() | (sub["parent_lv1"].str.lower() == "nan")
    sub.loc[mask_na, "parent_lv1"] = sub.loc[mask_na, "product_lv2"].map(LV2_TO_LV1)

    # aggregate capacity by (lv1_lv2 x status)
    g = (sub.groupby(["lv1_lv2","status"], dropna=False)["capacity"]
            .sum(min_count=1, numeric_only=True)
            .unstack("status")
            .reindex(columns=STATUS_ORDER, fill_value=0.0)
            .fillna(0.0))
    if g.empty:
        print("[capacity_vs_demand] No data after filtering.")
        return

    # parent per row: take prefix (everything before first underscore)
    # (safer than splitting labels elsewhere)
    g["__parent__"] = g.index.to_series().str.split("_", n=1, expand=True)[0]

    # demand per row (by parent lv1)
    g["__demand__"] = g["__parent__"].map(lambda k: demand.get(str(k), float("nan"))).astype(float)

    # totals & plotting matrix
    g["__total__"] = g[STATUS_ORDER].sum(axis=1)
    plot_mat = g[STATUS_ORDER].copy()

    # normalize to demand?
    if normalize_to_demand:
        denom = g["__demand__"].replace(0, 1).fillna(1.0)
        plot_mat = plot_mat.div(denom, axis=0)
        x_label = "Share of demand (100%)"
    else:
        x_label = "Capacity (units)"

    # sort by total (or total share)
    sort_vals = g["__total__"] if not normalize_to_demand else (
        g["__total__"] / g["__demand__"].replace(0, 1).fillna(1.0)
    )
    order = sort_vals.sort_values(ascending=False).index
    plot_mat = plot_mat.loc[order]
    g = g.loc[order]

    # colors
    color_list = [STATUS_COLORS.get(s, "#cccccc") for s in plot_mat.columns]

    # draw
    os.makedirs(os.path.dirname(outfile_png), exist_ok=True)
    ax = plot_mat.plot(kind="barh", stacked=True, figsize=figsize, color=color_list)
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel("product_lv1_lv2")

    # demand overlay
    if normalize_to_demand:
        ax.axvline(1.0, linestyle="--", linewidth=1)
    else:
        for i, key in enumerate(plot_mat.index):
            dval = float(g.loc[key, "__demand__"]) if pd.notna(g.loc[key, "__demand__"]) else None
            if dval and dval > 0:
                ax.vlines(dval, i - 0.4, i + 0.4, linestyles="--", linewidth=1)

    # legend & labels
    ax.legend(title="Status", frameon=False, bbox_to_anchor=(1.0, 0.5), loc="center left")
    plt.tight_layout(rect=[0, 0, 0.82, 1])

    # end labels
    for i, key in enumerate(plot_mat.index):
        total = g.loc[key, "__total__"]
        xpos = plot_mat.loc[key].sum()
        label = f"{xpos*100:.0f}%" if normalize_to_demand else f"{total:,.0f}"
        ax.text(xpos, i, f" {label}", va="center", fontsize=8)

    plt.savefig(outfile_png, dpi=dpi, bbox_inches="tight")
    plt.close()







# -----------------------------
# Usage
# -----------------------------
def output_plots():

    base_dir = Path(__file__).resolve().parent
    input_file = base_dir / "storage" / "input" / "unique_owners_filled.xlsx"
    output_dir = base_dir / "storage" / "figures"

    # ---- load data ----
    df_owner = pd.read_excel(input_file)
    df_owner["regionHQ"] = df_owner["countryHQ"].apply(map_region)
    df_main_flat = load_facility_df()
    df_merged = merge_owner(df_main_flat, df_owner)

    CONFIG = {
        "batches": [
            {
                "name": "capacities_by_status_country",
                "output_dir": str(output_dir / "COUNTRY"),
                "value_col": "capacity",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "status" },
                "filters": { "status": ["announced", "under construction", "operational"] },
                "index_by": ["iso2"],  # y-axis categories
                "plot": {
                    "order_by": "total_desc",
                    "orientation": "hbar",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "Capacity (units)"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Battery cells by status and country",        "filename": "battery_cells_status_country.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Battery modules/packs by status and country","filename": "battery_modules_status_country.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Solar cells by status and country",          "filename": "solar_cells_status_country.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Solar polysilicon by status and country",    "filename": "solar_polysilicon_status_country.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Solar ingot-wafers by status and country",   "filename": "solar_ingot_wafer_status_country.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Electric vehicles by status and country",    "filename": "electric_vehicles_status_country.png"}
                ]
            },
            {
                "name": "capacities_by_status_HQ",
                "output_dir": str(output_dir / "HQ"),
                "value_col": "capacity",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "status" },
                "filters": { "status": ["announced", "under construction", "operational"] },
                "index_by": ["regionHQ"],  # y-axis categories
                "plot": {
                    "order_by": "total_desc",
                    "top_n": None,
                    "orientation": "hbar",
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "Capacity (units)"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Battery cells by status and HQ",        "filename": "battery_cells_status_HQ.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Battery modules/packs by status and HQ","filename": "battery_modules_status_HQ.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Solar cells by status and HQ",          "filename": "solar_cells_status_HQ.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Solar polysilicon by status and HQ",    "filename": "solar_polysilicon_status_HQ.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Solar ingot-wafers by status and HQ",   "filename": "solar_ingot_wafer_status_HQ.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Electric vehicles by status and HQ",    "filename": "electric_vehicles_status_HQ.png"}
                ]
            },
                        {
                "name": "investments_construction_operational_HQ_country",
                "output_dir": str(output_dir / "HQ"),
                "value_col": "capacity",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "regionHQ" },
                "filters": { "status": [ "under construction", "operational"] },
                "index_by": ["iso2"],  # y-axis categories
                "plot": {
                    "order_by": "total_desc",
                    "top_n": None,
                    "normalize": False,
                    "orientation": "hbar",
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "Capacity (units)"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Capacity - Battery cells (under construction and operational) by country and HQ",        "filename": "capacity_battery_cells_country_HQ.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Capacity - Battery modules/packs (under construction and operational) by country and HQ","filename": "capacity_battery_modules_country_HQ.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Capacity - Solar cells by status (under construction and operational) by country and HQ",          "filename": "capacity_solar_country_HQ.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Capacity - Solar polysilicon (under construction and operational) by country and HQ",    "filename": "capacity_solar_polysilicon_countryHQ.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Capacity - Solar ingot-wafers(under construction and operational) by country and HQ",   "filename": "capacity_solar_ingot_wafer_country_HQ.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Capacity - Electric vehicles (under construction and operational) by country and HQ",    "filename": "capacity_electric_vehicles_country_HQ.png"}
                ]
            },
            {
                "name": "investments_construction_operational_HQ_country",
                "output_dir": str(output_dir / "HQ"),
                "value_col": "capacity",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "regionHQ" },
                "filters": { "status": [ "announced"] },
                "index_by": ["iso2"],  # y-axis categories
                "plot": {
                    "order_by": "total_desc",
                    "orientation": "hbar",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "Capacity (units)"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Capacity - Battery cells (announced) by country and HQ",        "filename": "capacity_battery_cells_announced_country_HQ.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Capacity - Battery modules/packs (announced)  by country and HQ","filename": "capacity_battery_modules_rannounced_country_HQ.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Capacity - Solar cells by status (announced)  by country and HQ",          "filename": "capacity_solar_announced_country_HQ.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Capacity - Solar polysilicon (announced)  by country and HQ",    "filename": "capacity_solar_polysilicon_announced_countryHQ.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Capacity - Solar ingot-wafers(announced)  by country and HQ",   "filename": "capacity_solar_ingot_wafer_announced_country_HQ.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Capacity -Electric vehicles(announced) by country and HQ",    "filename": "capacity_electric_vehicles_announced_country_HQ.png"}
                ]
            },
            {
                "name": "capacity_company_status",
                "output_dir": str(output_dir / "COMPANY"),
                "value_col": "capacity",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "status" },
                "filters": { "status": [ "announced", "under construction", "operational"] },
                "index_by": ["master"],  # y-axis categories
                "plot": {
                    "order_by": "total_desc",
                    "orientation": "hbar",
                    "top_n": 20,
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "Capacity (units)"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Capacity - Battery cells by company and status",        "filename": "capacity_battery_cells_announced_company_status.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Capacity - Battery modules/packs by company and status","filename": "capacity_battery_modules_rannounced_company_status.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Capacity - Solar cells by status by company and status",          "filename": "capacity_solar_announced_company_status.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Capacity - Solar polysilicon by company and status",    "filename": "capacity_solar_polysilicon_announced_company_status.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Capacity - Solar ingot-wafers by company and status",   "filename": "capacity_solar_ingot_wafer_announced_company_status.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Capacity -Electric vehicles by company and status",    "filename": "capacity_electric_vehicles_announced_company_status.png"}
                ]
            },
            {
                "name": "capacity_company_iso_under_construction_operational",
                "output_dir": str(output_dir / "COMPANY"),
                "value_col": "capacity",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "iso2" },
                "filters": { "status": [ "under construction", "operational"] },
                "index_by": ["master"],  # y-axis categories
                "plot": {
                    "order_by": "total_desc",
                    "orientation": "hbar",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "Capacity (units)"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Capacity - Battery cells under consutuction and operational by company and country",        "filename": "capacity_battery_cells_construction_operational_company_country.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Capacity - Battery modules/packs  under consutuction and operational by company and country","filename": "capacity_battery_modules_construction_operational_company_country.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Capacity - Solar cells under consutuction and operational by company and country",          "filename": "capacity_solar_announced_construction_operational_company_country.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Capacity -- Solar polysilicon  under consutuction and operational by company and country",    "filename": "capacity_solar_polysilicon_construction_operational_company_country.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Capacity - Solar ingot-wafers under consutuction and operational by company and country",   "filename": "capacity_solar_ingot_wafer_construction_operational_company_country.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Capacity --Electric vehicles under consutuction and operational by company and country",    "filename": "capacity_electric_vehicles_construction_operational_company_country.png"}
                ]
            },
            {
                "name": "capacity_company_iso_under_construction_operational",
                "output_dir": str(output_dir / "COMPANY"),
                "value_col": "capacity",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "iso2" },
                "filters": { "status": [ "announced"] },
                "index_by": ["master"],  # y-axis categories
                "plot": {
                    "order_by": "total_desc",
                    "orientation": "hbar",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "Capacity (units)"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Capacity - Battery cells announced by company and country",        "filename": "capacity_battery_cells_announced_company_country.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Capacity - Battery modules/packs announced  by company and country","filename": "capacity_battery_modules_announced_company_country.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Capacity - Solar cells announced  by company and country",          "filename": "capacity_solar_announced_announced_company_country.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Capacity -- Solar polysilicon announced by company and country",    "filename": "capacity_solar_polysilicon_announced_company_country.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Capacity - Solar ingot-wafers announced  by company and country",   "filename": "capacity_solar_ingot_wafer_announced_company_country.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Capacity --Electric vehicles announced by company and country",    "filename": "capacity_electric_vehicle_announced_company_country.png"}
                ]
            },
    # Capacity quarter plots ----------
                            {
                "name": "capacity_quarter_announced",
                "output_dir": str(output_dir / "QUARTER"),
                "value_col": "capacity",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "status", "order": ["announced","under construction","operational"] },
                "filters": {"status": [ "under construction", "operational",  "announced"] },
                "index_by": ["announced_on_quarter"],  # y-axis categories
                "plot": {
                    "orientation": "vbar",
                    "order_by": "index_asc",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "announced quarter"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Capacity - Battery cells  by quarter",        "filename": "capacity_battery_cells_announced_quarter.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Capacity- Battery modules/packs by quarter","filename": "capacity_battery_modules_announced_quarter.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Capacity - Solar cells  by quarter",          "filename": "capacity_solar_announced_quarter.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Capacity- Solar polysilicon   by quarter",    "filename": "capacity_solar_polysilicon_announced_quarter.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Capacity - Solar ingot-wafers  by quarter",   "filename": "capacity_solar_ingot_wafer_announced_quarter.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Capacity -Electric vehicles by quarter",    "filename": "capacity_electric_vehicles_announced_quarter.png"}
                ]
            },
                        {
                "name": "capacity_quarter_under_construction_operational",
                "output_dir": str(output_dir / "QUARTER"),
                "value_col": "capacity",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "status", "order": ["announced","under construction","operational"] },
                "filters": {"status": [ "under construction", "operational"] },
                "index_by": ["announced_on_quarter"],  # y-axis categories
                "plot": {
                    "orientation": "vbar",
                    "order_by": "index_asc",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False, 
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "announced quarter"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Capacity - Battery cells under construction and operational by quarter",        "filename": "capacity_battery_cells_construction_operational_quarter.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Capacity- Battery modules/packs construction and operational by quarter","filename": "capacity_battery_modules_construction_operational_quarter.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Capacity - Solar cells construction and operational by quarter",          "filename": "capacity_solar_construction_operational_announced_quarter.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Capacity- Solar polysilicon  construction and operational by quarter",    "filename": "capacity_solar_polysilicon_construction_operational_quarter.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Capacity - Solar ingot-wafers construction and operational by quarter",   "filename": "capacity_solar_ingot_wafer_construction_operational_quarter.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Capacity -Electric vehicles construction and operational by quarter",    "filename": "capacity_electric_vehicles_construction_operational_quarter.png"}
                ]
            },

            #-------------------------------------------------
            # Investment plots 
            #-------------------------------------------------
            {
                "name": "investments_by_status_country",
                "output_dir": str(output_dir / "COMPANY"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "status" },
                "filters": { "status": ["announced", "under construction", "operational"] },
                "index_by": ["iso2"],  # y-axis categories
                "plot": {
                    "order_by": "total_desc",
                    "top_n": None,
                    "orientation": "hbar",
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "EUR"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Investment - Battery cells by status and country",        "filename": "investment_battery_cells_status_country.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Investment - Battery modules/packs by status and country","filename": "investment_battery_modules_status_country.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Investment - Solar cells by status and country",          "filename": "investment_solar_cells_status_country.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Investment - Solar polysilicon by status and country",    "filename": "investment_solar_polysilicon_status_country.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Investment - Solar ingot-wafers by status and country",   "filename": "investment_solar_ingot_wafer_status_country.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Investment -Electric vehicles by status and country",    "filename": "investment_electric_vehicles_status_country.png"}
                ]
            },
            {
                "name": "invetsments_by_status_HQ",
                "output_dir": str(output_dir / "HQ"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "status" },
                "filters": { "status": ["announced", "under construction", "operational"] },
                "index_by": ["regionHQ"],  # y-axis categories
                "plot": {
                    "order_by": "total_desc",
                    "orientation": "hbar",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "EUR"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Investment - Battery cells by status and HQ",        "filename": "investment_battery_cells_status_HQ.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Investment - Battery modules/packs by status and HQ","filename": "investment_battery_modules_status_HQ.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Investment - Solar cells by status and HQ",          "filename": "investment_solar_cells_status_HQ.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Investment - Solar polysilicon by status and HQ",    "filename": "investment_solar_polysilicon_status_HQ.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Investment - Solar ingot-wafers by status and HQ",   "filename": "investment_solar_ingot_wafer_status_HQ.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Investment - Electric vehicles by status and HQ",    "filename": "investment_electric_vehicles_status_HQ.png"}
                ]
            },
            {
                "name": "investments_construction_operational_HQ_country",
                "output_dir": str(output_dir / "HQ"),
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "regionHQ" },
                "filters": { "status": [ "under construction", "operational"] },
                "index_by": ["iso2"],  # y-axis categories
                "plot": {
                    "order_by": "total_desc",
                    "orientation": "hbar",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "EUR"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Investment - Battery cells (under construction and operational) by country and HQ",        "filename": "investment_battery_cells_country_HQ.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Investment - Battery modules/packs (under construction and operational) by country and HQ","filename": "investment_battery_modules_country_HQ.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Investment - Solar cells by status (under construction and operational) by country and HQ",          "filename": "investment_solar_country_HQ.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Investment - Solar polysilicon (under construction and operational) by country and HQ",    "filename": "investment_solar_polysilicon_countryHQ.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Investment - Solar ingot-wafers(under construction and operational) by country and HQ",   "filename": "investment_solar_ingot_wafer_country_HQ.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Investment - Electric vehicles (under construction and operational) by country and HQ",    "filename": "investment_electric_vehicles_country_HQ.png"}
                ]
            },
            {
                "name": "investments_construction_operational_HQ_country",
                "output_dir": str(output_dir / "HQ"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "regionHQ" },
                "filters": { "status": [ "announced"] },
                "index_by": ["iso2"],  # y-axis categories
                "plot": {
                    "order_by": "total_desc",
                    "orientation": "hbar",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "EUR"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Investment - Battery cells (announced) by country and HQ",        "filename": "investment_battery_cells_announced_country_HQ.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Investment - Battery modules/packs (announced)  by country and HQ","filename": "investment_battery_modules_rannounced_country_HQ.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Investment - Solar cells by status (announced)  by country and HQ",          "filename": "investment_sola_announced_country_HQ.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Investment - Solar polysilicon (announced)  by country and HQ",    "filename": "investment_solar_polysilicon_announced_countryHQ.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Investment - Solar ingot-wafers(announced)  by country and HQ",   "filename": "investment_solar_ingot_wafer_announced_country_HQ.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Investment - Electric vehicles(announced) by country and HQ",    "filename": "investment_electric_vehicles_announced_country_HQ.png"}
                ]
            },
            {
                "name": "investments_company_status",
                "output_dir": str(output_dir / "COMPANY"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "status" },
                "filters": { "status": [ "announced", "under construction", "operational"] },
                "index_by": ["master"],  # y-axis categories
                "plot": {
                    "order_by": "total_desc",
                    "top_n": None,
                    "normalize": False,
                    "orientation": "hbar",
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "EUR"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Investment - Battery cells by company and status",        "filename": "investment_battery_cells_company_status.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Investment- Battery modules/packs by company and status","filename": "investment_battery_modules_company_status.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Investment - Solar cells by company and status",          "filename": "investment_solar_company_status.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Investment - Solar polysilicon by company and status",    "filename": "investment_solar_polysilicon_company_status.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Investment - Solar ingot-wafers by company and status",   "filename": "investment_solar_ingot_wafer_company_status.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Investment -Electric vehicles by company and status",    "filename": "investment_electric_vehicles_company_status.png"}
                ]
            },
            {
                "name": "investments_company_country_under_construction_operational",
                "output_dir": str(output_dir / "COMPANY"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "iso2" },
                "filters": { "status": [ "under construction", "operational"] },
                "index_by": ["master"],  # y-axis categories
                "plot": {
                    "order_by": "total_desc",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": True,
                    "orientation": "hbar",
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "EUR"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Investment - Battery cells under consutuction and operational by company and country",        "filename": "investment_battery_cells_construction_operational_company_country.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Investment- Battery modules/packs  under consutuction and operational by company and country","filename": "investment_battery_modules_construction_operational_company_country.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Investment - Solar cells under consutuction and operational by company and country",          "filename": "investment_solar_announced_construction_operational_company_country.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Investment - Solar polysilicon  under consutuction and operational by company and country",    "filename": "investment_solar_polysilicon_construction_operational_company_country.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Investment - Solar ingot-wafers under consutuction and operational by company and country",   "filename": "investment_solar_ingot_wafer_construction_operational_company_country.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Investment -Electric vehicles under consutuction and operational by company and country",    "filename": "investment_electric_vehicles_construction_operational_company_country.png"}
                ]
            },
            {
                "name": "investments_company_country_announced",
                "output_dir": str(output_dir / "COMPANY"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "iso2" },
                "filters": { "status": [ "announced"] },
                "index_by": ["master"],  # y-axis categories
                "plot": {
                    "order_by": "total_desc",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "orientation": "hbar",
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "EUR"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Investment - Battery cells announced by company and country",        "filename": "investment_battery_cells_announced_company_country.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Investment- Battery modules/packs  announced by company and country","filename": "investment_battery_modules_announced_country.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Investment - Solar cells announced by company and country",          "filename": "investment_solar_announced_announced_country.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Investment - Solar polysilicon  announced by company and country",    "filename": "investment_solar_polysilicon_announced_country.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Investment - Solar ingot-wafers announced by company and country",   "filename": "investment_solar_ingot_wafer_announced_company_country.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Investment -Electric vehicles announced by company and country",    "filename": "investment_electric_vehicles_announced_company_country.png"}
                ]
            },
            #----------Investment quarters-----------------------------------------
            {
                "name": "investments_quarter_announced",
                "output_dir":str(output_dir / "QUARTER"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "status", "order": ["announced","under construction","operational"] },
                "filters": {"status": [ "announced", "under construction", "operational"] },
                "index_by": ["announced_on_quarter"],  # y-axis categories
                "plot": {
                    "orientation": "vbar",
                    "order_by": "index_asc",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "annouced quarter"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Investment - Battery cells announced by quarter",        "filename": "investment_battery_cells_announced_quarter.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Investment- Battery modules/packs  announced by quarter","filename": "investment_battery_modules_announced_quarter.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Investment - Solar cells announced by quarter",          "filename": "investment_solar_announced_announced_quarter.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Investment - Solar polysilicon  announced by quarter",    "filename": "investment_solar_polysilicon_announced_quarter.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Investment - Solar ingot-wafers announced by quarter",   "filename": "investment_solar_ingot_wafer_announced__quarter.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Investment -Electric vehicles announced by quarter",    "filename": "investment_electric_vehicles_announced_quarter.png"}
                ]
            },
                        {
                "name": "investments_quarter_under_construction_operational",
                "output_dir": str(output_dir / "QUARTER"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "status", "order": ["announced","under construction","operational"] },
                "filters": {"status": [ "under construction", "operational"] },
                "index_by": ["announced_on_quarter"],  # y-axis categories
                "plot": {
                    "orientation": "vbar",
                    "order_by": "index_asc",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "announced quarter"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Investment - Battery cells under construction and operational by quarter",        "filename": "investment_battery_cells_construction_operational_quarter.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Investment- Battery modules/packs construction and operational by quarter","filename": "investment_battery_modules_construction_operational_quarter.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Investment - Solar cells construction and operational by quarter",          "filename": "investment_solar_construction_operational_announced_quarter.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Investment - Solar polysilicon  construction and operational by quarter",    "filename": "investment_solar_polysilicon_construction_operational_quarter.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Investment - Solar ingot-wafers construction and operational by quarter",   "filename": "investment_solar_ingot_wafer_construction_operational_quarter.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Investment -Electric vehicles construction and operational by quarter",    "filename": "investment_electric_vehicles_construction_operational_quarter.png"}
                ]
            },
            # All tech capacity--------------------------------------------------
            {
            "name": "capacity_by_productlv1_country_construction_operational",
            "output_dir": str(output_dir / "COUNTRY"),
            "value_col": "capacity",
            "stack": { "column": "product_lv1" },
            "filters": { "status": ["under construction", "operational"], "product_lv1": ["battery", "vehicle", "solar"]  },
            "index_by": ["iso2"],
            "plot": {
                "order_by": "total_desc",
                "orientation": "hbar",
                "normalize": False,
                "show_value_labels": True,
                "legend_outside": False,
                "legend_ncol": 2,
                "dpi": 300,
                "figsize": [11, 7],
                "x_unit": "Capacity (units)"
            },
            "charts": [
                {"lv1": "ALL", "lv2": "ALL", "title": "Capacity by country (stacked by product level 1)", "filename": "capacity_by_country_stack_lv1_construction_operational.png"}
            ]
            },
            {
                "name": "capacity_by_productlv1_HQ_construction_operational",
                "output_dir": str(output_dir / "HQ"),
                "value_col": "capacity",
                "stack": { "column": "product_lv1" },
                "filters": { "status": ["under construction", "operational"], "product_lv1": ["battery", "vehicle", "solar"]  },
                "index_by": ["regionHQ"],
                "plot": {
                    "order_by": "total_desc",
                    "orientation": "hbar",
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "Capacity (units)"
                },
                "charts": [
                    {"lv1": "ALL", "lv2": "ALL", "title": "Capacity by HQ region (stacked by product level 1)", "filename": "capacity_by_HQ_stack_lv1_construction_operational.png"}
                ]
            },
            {
                "name": "capacity_quarter_by_productlv1_construction_operational",
                "output_dir": str(output_dir / "QUARTER"),
                "value_col": "capacity",
                "stack": { "column": "product_lv1" },
                "filters": { "status": ["under construction", "operational"], "product_lv1": ["battery", "vehicle", "solar"] },
                "index_by": ["announced_on_quarter"],
                "plot": {
                    "orientation": "vbar",
                    "order_by": "index_asc",
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "Announced quarter"
                },
                "charts": [
                    {"lv1": "ALL", "lv2": "ALL", "title": "Capacity by quarter (stacked by product level 1)", "filename": "capacity_quarter_stack_lv1_construction_operational.png"}
                ]
            },
            # All tech investment--------------------------------------------------
            {
                "name": "investment_by_productlv1_country_construction_operational",
                "output_dir": str(output_dir / "COUNTRY"),
                "value_col": "investment",
                "stack": { "column": "product_lv1" },
                "filters": { "status": ["under construction", "operational"], "product_lv1": ["battery", "vehicle", "solar"] },
                "index_by": ["iso2"],
                "plot": {
                    "order_by": "total_desc",
                    "orientation": "hbar",
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "EUR"
                },
                "charts": [
                    {"lv1": "ALL", "lv2": "ALL", "title": "Investment by country (stacked by product level 1)", "filename": "investment_by_country_stack_lv1_construction_operational.png"}
                ]
            },
            {
                "name": "investment_by_productlv1_HQ_construction_operational",
                "output_dir": str(output_dir / "HQ"),
                "value_col": "investment",
                "stack": { "column": "product_lv1" },
                "filters": { "status": ["under construction", "operational"],  "product_lv1": ["battery", "vehicle", "solar"] },
                "index_by": ["regionHQ"],
                "plot": {
                    "order_by": "total_desc",
                    "orientation": "hbar",
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "EUR"
                },
                "charts": [
                    {"lv1": "ALL", "lv2": "ALL", "title": "Investment by HQ region (stacked by product level 1)", "filename": "investment_by_HQ_stack_lv1_construction_operational.png"}
                ]
            },
            {
                "name": "investment_quarter_by_productlv1_construction_operational",
                "output_dir": str(output_dir / "QUARTER"),
                "value_col": "investment",
                "stack": { "column": "product_lv1" },
                "filters": { "status": ["under construction", "operational"] ,  "product_lv1": ["battery", "vehicle", "solar"]},
                "index_by": ["announced_on_quarter"],
                "plot": {
                    "orientation": "vbar",
                    "order_by": "index_asc",
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "Announced quarter"
                },
                "charts": [
                    {"lv1": "ALL", "lv2": "ALL", "title": "Investment by quarter (stacked by product level 1)", "filename": "investment_quarter_stack_lv1_construction_operational.png"}
                ]
            }

        ]
    }
    output_plots_from_config(df_merged, CONFIG)

    # -----------------------------
    # Demand comparison charts
    # -----------------------------
    demand = {
        "battery": 410,          # GWh
        "solar": 58,             # GW
        "vehicles": 2_300_000,   # units
    }

    comp_dir = output_dir / "COMPARISONS"
    comp_dir.mkdir(parents=True, exist_ok=True)

    plot_capacity_vs_demand_lv2(
        df=df_merged,
        demand=demand,
        outfile_png=str(comp_dir / "capacity_vs_demand_lv2_percent.png"),
        include_lv2=["cell", "module_pack", "ingot_wafer", "polysilicon", "electric"],
        status_filter=["operational", "under construction", "announced"],
        normalize_to_demand=True,
        title="Capacity vs demand by product LV2 (share of demand)"
    )

    plot_capacity_vs_demand_lv2(
        df=df_merged,
        demand=demand,
        outfile_png=str(comp_dir / "capacity_vs_demand_lv2_absolute.png"),
        include_lv2=["cell", "module_pack", "ingot_wafer", "polysilicon", "electric"],
        status_filter=["operational", "under construction", "announced"],
        normalize_to_demand=False,
        title="Capacity vs demand by product LV2 (absolute, dashed = demand)"
    )





