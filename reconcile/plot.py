# -*- coding: utf-8 -*-
import sys; sys.path.append("..")

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, List, Union

# from mongo_client import facilities_collection
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

# -----------------------------
import os
from typing import Dict, List, Tuple

import sys; sys.path.append("..")

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Any, Union

# from mongo_client import facilities_collection
from src.config import CAPACITIES_PLOT

# mongo_client_setup.py
import os
import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import logging

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
ARTICLES_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME")
FACILITIES_COLLECTION = "facilities_develop" #os.getenv("MONGO_FACILITIES_COLLECTION") change later


if not all([MONGO_URI, DB_NAME, ARTICLES_COLLECTION_NAME]):
    raise RuntimeError("❌ Missing required MongoDB environment variables.")

mongo_client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
db = mongo_client[DB_NAME]
articles_collection = db[ARTICLES_COLLECTION_NAME]
facilities_collection = db[FACILITIES_COLLECTION]
geonames_collection = db["geonames_store"]

geonames_collection = db["geonames_lookup"]

def test_mongo_connection():
    try:
        mongo_client.admin.command("ping")
        print("✅ Connected to MongoDB Atlas!")
    except Exception as e:
        print(f"❌ MongoDB Connection Error: {e}")
        raise


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
    df["product_lv2"] = df["product_lv2"].apply(lambda x: x if isinstance(x, list) else ([x] if x is not None else [pd.NA]))
    df = df.explode("product_lv2", ignore_index=True)

    # dates
    date_cols = ["announced_on", "under_construction_on", "operational_on"]
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    # coerce capacities if objects slipped in
    for c in ["capacity", "investment"]:
        if c in df.columns and df[c].dtype == "object":
            df[c] = pd.to_numeric(df[c], errors="coerce")

    output_cols = [
        "iso2","adm1","owner","product_lv1","product_lv2","status","capacity","investment",
        "announced_on","under_construction_on","operational_on"
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
    'Romania','Slovakia','Slovenia','Spain','Sweden', 'Norway', 'United Kingdom'
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
    elif country == "India":
        return "India"
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

    overlap = set(df["owner"].dropna().unique()) & set(owner["owner"].dropna().unique())
    print(f"- overlap of keys: {len(overlap)}")


    # Do the merge with indicator to see what happened
    merged = df.merge(owner, on="owner", how="left", suffixes=("", "_owner"), indicator=True)

    print("\n[merge_owner] Merge indicator breakdown:")
    print(merged["_merge"].value_counts(dropna=False))

    # Show a few unmatched left keys
    left_only_keys = merged.loc[merged["_merge"] == "left_only", "owner"].dropna().unique()
    if len(left_only_keys):
        print(f"[merge_owner] Sample unmatched df.owner keys): {left_only_keys}")
    

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
from matplotlib.ticker import FuncFormatter

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
    """
    Plot a stacked bar chart from a wide pivot table.
    Falls back to a single unstacked 'Total' bar if no stack components survive filters.
    Supports optional legend label renaming via plot_cfg["legend_labels"].
    If plot_cfg["format_x_millions"] is True (and not normalized), axis ticks + labels show millions.
    Optional: plot_cfg["currency_prefix"] = "€" / "$" / "".
    """
    if pivot.empty:
        print(f"[skip] No data to plot for: {title}")
        return

    if "total__" not in pivot.columns:
        pivot["total__"] = pivot.sum(axis=1, numeric_only=True)

    # ------------------ Ordering ------------------
    order_by = plot_cfg.get("order_by", "total_desc")
    order_on = plot_cfg.get("order_on_stack_value")
    order_dir = str(plot_cfg.get("order_direction", "desc")).lower()
    ascending = (order_dir == "asc")

    if order_on is not None:
        order_cols = [order_on] if isinstance(order_on, (str, int)) else list(order_on)
        order_cols = [c for c in order_cols if c in pivot.columns]
        if order_cols:
            pivot = pivot.sort_values(by=order_cols, ascending=ascending)
        else:
            print(f"[warn] order_on_stack_value {order_on} not found; falling back to total.")
            pivot = pivot.sort_values(by="total__", ascending=False)
    else:
        if order_by == "total_desc":
            pivot = pivot.sort_values(by="total__", ascending=False)
        elif order_by == "total_asc":
            pivot = pivot.sort_values(by="total__", ascending=True)
        elif order_by == "index_asc":
            pivot = pivot.sort_index(ascending=True)
        elif order_by == "index_desc":
            pivot = pivot.sort_index(ascending=False)
        else:
            pivot = pivot.sort_values(by="total__", ascending=False)

    # ------------------ Limit to top N ------------------
    top_n = plot_cfg.get("top_n")
    if isinstance(top_n, int) and top_n > 0:
        pivot = pivot.head(top_n)

    # ------------------ Select stack columns ------------------
    stack_cols = [c for c in pivot.columns if c != "total__"]

    # Drop all-zero stacks (e.g., filtered away)
    stack_cols = [c for c in stack_cols if (pivot[c].sum(numeric_only=True) if hasattr(pivot[c], "sum") else 0) > 0]

    # Normalize option
    normalize = bool(plot_cfg.get("normalize", False))

    # If nothing left to stack, plot a single unstacked "Total" column
    if not stack_cols:
        total_label = plot_cfg.get("total_label", "Total")
        pivot_plot = pivot[["total__"]].rename(columns={"total__": total_label})
        stacked = False
        # Normalization doesn't make sense without components
        normalize = False
        value_axis_label = plot_cfg.get("x_unit", "Value")
    else:
        # ------------------ Normalize if requested ------------------
        if normalize:
            denom = pivot[stack_cols].sum(axis=1).replace(0, 1)
            pivot_plot = pivot[stack_cols].div(denom, axis=0)
            value_axis_label = "Share (100%)"
        else:
            pivot_plot = pivot[stack_cols]
            value_axis_label = plot_cfg.get("x_unit", "Value")
        stacked = True

    # ------------------ Figure params ------------------
    figsize = tuple(plot_cfg.get("figsize", (10, 6)))
    dpi = int(plot_cfg.get("dpi", 300))
    os.makedirs(os.path.dirname(outfile_png), exist_ok=True)

    # Colors
    color_kw = {}
    if stack_colors and len(pivot_plot.columns) > 1:  # only makes sense with multiple stacks
        color_kw["color"] = [stack_colors.get(c, "#cccccc") for c in pivot_plot.columns]

    orientation = str(plot_cfg.get("orientation", "hbar")).lower()
    kind = "barh" if orientation == "hbar" else "bar"

    ax = pivot_plot.plot(kind=kind, stacked=stacked, figsize=figsize, **color_kw)

    # Axis labels
    if orientation == "hbar":
        ax.set_xlabel(value_axis_label)
        ax.set_ylabel(index_label or "Index")
    else:
        ax.set_xlabel(index_label or "Index")
        ax.set_ylabel(value_axis_label)

    ax.set_title(title)

    # ------------------ Legend with optional renaming ------------------
    handles, labels = ax.get_legend_handles_labels()
    legend_labels = plot_cfg.get("legend_labels", {})  # {"operational": "Operating", ...}
    if legend_labels:
        labels = [legend_labels.get(l, l) for l in labels]

    # Hide legend when there’s only one column unless forced
    if len(pivot_plot.columns) <= 1 and not plot_cfg.get("force_legend", False):
        leg = ax.get_legend()
        if leg:
            leg.remove()
    else:
        if plot_cfg.get("legend_outside", True):
            ncol = int(plot_cfg.get("legend_ncol", 1))
            ax.legend(
                handles, labels,
                loc="center left",
                bbox_to_anchor=(1.0, 0.5),
                frameon=False, ncol=ncol,
                title=legend_title or "Legend",
            )
            plt.tight_layout(rect=[0, 0, 0.8, 1])
        else:
            leg = ax.legend(handles, labels, title=legend_title or "Legend")
            if leg:
                leg.set_frame_on(False)
            plt.tight_layout()

    # ------------------ MILLIONS formatting (investment only) ------------------
    format_millions = bool(plot_cfg.get("format_x_millions", False))
    currency = plot_cfg.get("currency_prefix", "")
    if format_millions and not normalize:
        fmt = FuncFormatter(lambda x, pos: f"{currency}{x/1_000_000:,.0f}")
        if orientation == "hbar":
            ax.xaxis.set_major_formatter(fmt)
            unit = plot_cfg.get("x_unit", "").strip()
            label = f"{unit} (million)" if unit else "Million"
            ax.set_xlabel(label)
        else:
            ax.yaxis.set_major_formatter(fmt)
            unit = plot_cfg.get("x_unit", "").strip()
            label = f"{unit} (million)" if unit else "Million"
            ax.set_ylabel(label)

    # ------------------ Value labels ------------------
    show_labels = plot_cfg.get("show_value_labels", True)
    if show_labels:
        if orientation == "hbar":
            for i, (idx, _) in enumerate(pivot_plot.iterrows()):
                total_val = 1.0 if normalize else pivot.loc[idx, "total__"]
                if normalize:
                    label = f"{(pivot_plot.loc[idx].sum())*100:.0f}%"
                    xpos = pivot_plot.loc[idx].sum()
                    ax.text(xpos, i, f" {label}", va="center", fontsize=8)
                else:
                    if format_millions:
                        label = f"{currency}{total_val/1_000_000:,.1f}M"
                    else:
                        label = f"{total_val:,.0f}"
                    xpos = pivot_plot.loc[idx].sum()
                    ax.text(xpos, i, f" {label}", va="center", fontsize=8)
        else:
            for i, idx in enumerate(pivot_plot.index):
                total_val = 1.0 if normalize else pivot.loc[idx, "total__"]
                if normalize:
                    label = f"{(pivot_plot.loc[idx].sum())*100:.0f}%"
                    ypos = pivot_plot.loc[idx].sum()
                    ax.text(i, ypos, f"{label}", ha="center", va="bottom", fontsize=8)
                else:
                    if format_millions:
                        label = f"{currency}{total_val/1_000_000:,.1f}M"
                    else:
                        label = f"{total_val:,.0f}"
                    ypos = pivot_plot.loc[idx].sum()
                    ax.text(i, ypos, f"{label}", ha="center", va="bottom", fontsize=8)

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
    Skips gracefully (returns empty DF) if needed columns are missing.
    """
    sub = df.copy()

    # Optional filtering on lv1/lv2
    if lv1 not in (None, "ALL", "*"):
        if "product_lv1" not in sub.columns:
            print(f"[skip] Missing column 'product_lv1' for lv1={lv1}")
            return pd.DataFrame()
        sub = sub[sub["product_lv1"] == lv1]

    if lv2 not in (None, "ALL", "*"):
        if "product_lv2" not in sub.columns:
            print(f"[skip] Missing column 'product_lv2' for lv2={lv2}")
            return pd.DataFrame()
        sub = sub[sub["product_lv2"] == lv2]

    if sub.empty:
        return pd.DataFrame()

    # ---- Requirements check
    needed_cols = set(index_by) | {stack_col, value_col}
    missing = [c for c in needed_cols if c not in sub.columns]
    if missing:
        print(f"[skip] Missing columns {missing} for lv1={lv1}, lv2={lv2}; skipping chart")
        return pd.DataFrame()

    # Ensure numeric value_col (coerce if needed)
    if not np.issubdtype(sub[value_col].dtype, np.number):
        sub[value_col] = pd.to_numeric(sub[value_col], errors="coerce")

    # If everything is NaN after coercion, skip
    if sub[value_col].notna().sum() == 0:
        print(f"[skip] '{value_col}' has no numeric values after coercion; skipping chart")
        return pd.DataFrame()

    group_by = _dedup_seq(list(index_by) + [stack_col])

    grouped = (
        sub.groupby(group_by, dropna=False)[value_col]
           .sum(min_count=1, numeric_only=True)
           .reset_index()
    )

    # If grouping produced no rows (all NaN summed out), skip
    if grouped.empty:
        return pd.DataFrame()

    pivot = (
        grouped.pivot_table(index=index_by, columns=stack_col, values=value_col, fill_value=0.0)
               .fillna(0.0)
    )

    # Respect declared stack order first, then append leftovers
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
    sub = df.copy()
    for key, val in (filters or {}).items():
        if key.endswith(("_min", "_max", "_not", "_regex")):
            base = key.rsplit("_", 1)[0]
        else:
            base = key

        # >>> SKIP if the column doesn't exist
        if base not in sub.columns:
            print(f"[skip][filters] column '{base}' not in DataFrame; skipping this filter")
            continue

        if key.endswith("_min"):
            sub = sub[sub[base] >= val]
        elif key.endswith("_max"):
            sub = sub[sub[base] <= val]
        elif key.endswith("_not"):
            vals = val if isinstance(val, (list, tuple, set)) else [val]
            sub = sub[~sub[base].isin(vals)]
        elif key.endswith("_regex"):
            sub = sub[sub[base].astype(str).str.contains(val, case=False, regex=True, na=False)]
        else:
            vals = val if isinstance(val, (list, tuple, set)) else [val]
            sub = sub[sub[base].isin(vals)]
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
        if stack_col not in df_use.columns:
            df_use[stack_col] = "Total"
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
    # # Keep only rows where product_lvl1 contains "vehicle battery" or "solar"
    # df_main_flat = df_main_flat[
    #     df_main_flat["product_lv1"].isin(["vehicle", "battery", "solar"])
    # ]

    df_merged = merge_owner(df_main_flat, df_owner)
    # save to Excel

    cutoff = pd.Timestamp("2021-01-01")

    # df_merged = df_merged[
    #     (
    #         (df_merged["announced_on"] >= cutoff)
    #     )
    #     |
    #     (
    #         (df_merged["announced_on"].isna()) & 
    #         ((df_merged["under_construction_on"] - pd.DateOffset(years=2)) >= cutoff )
    #     )
    # ]


    # df_merged = df_merged[
    #     (
    #         (df_merged["announced_on"] >= cutoff)
    #     )
    # ]
    merged_path = Path("storage/output/df_merged.xlsx")  # pick your folder
    merged_path.parent.mkdir(parents=True, exist_ok=True)
    df_merged.to_excel(merged_path, index=False)
    print(f"Saved merged plotting dataset to: {merged_path.resolve()}")

    CONFIG = {
        "batches": [
            {
            "name": "capacities_by_status_country",
            "output_dir": str(output_dir / "VF"),
            "value_col": "investment",
            "stack": {"column": "__all__"},  # <- sum across everything,  # stacks on "status" by default
            "filters": {
                "status": ["announced", "under construction", "operational"],
                "product_lv1": ["vehicle", "solar", "battery"],
                "product_lv2": ["ingot_wafer", "cell", "electric"]
            },
            "index_by": ["iso2"],
            "index_label": "Country",
            "plot": {
                "order_direction": "desc",
                "orientation": "hbar",
                "normalize": False,
                "show_value_labels": False,
                "legend_outside": False,
                "legend_ncol": 2,
                "dpi": 300,
                "figsize": [11, 7],
                "x_unit": "EUR",
                "format_x_millions": True,
                "currency_prefix": "€",
                "total_label": "Total investment",
                "force_legend": False
            },
            "charts": [
                {"lv1": "ALL", "lv2": "ALL", "title": "", "filename": "f.png"}
            ]
            },
                       {
            "name": "capacities_by_status_country",
            "output_dir": str(output_dir / "VF"),
            "value_col": "investment",
            "stack": {"column": "__all__"},  # <- sum across everything,  # stacks on "status" by default
            "filters": { "status": [ "announced", "under construction", "operational"], "product_lv1": ["vehicle", "solar", "battery"],"product_lv2": ["ingot_wafer", "cell", "electric"] },
            "index_by": ["status"],
            "index_label": "status",
            "plot": {
                "order_direction": "desc",
                "orientation": "hbar",
                "normalize": False,
                "show_value_labels": True,
                "legend_outside": False,
                "legend_ncol": 2,
                "dpi": 300,
                "figsize": [11, 7],
                "x_unit": "EUR",
                "format_x_millions": True,
                "currency_prefix": "€",
                "total_label": "Total investment",
                "force_legend": False
            },
            "charts": [
                {"lv1": "ALL", "lv2": "ALL", "title": "", "filename": "m.png"}
            ]
            },
            {
                "name": "capacities_by_status_country",
                "output_dir": str(output_dir / "VF"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "status", "order": ["operational", "under construction", "announced"] },
                "filters": { "status": [ "operational", "under construction", "announced"], "product_lv1": ["vehicle", "solar", "battery"],"product_lv2": ["ingot_wafer", "cell", "electric"] },
                "index_by": ["iso2"], 
                "index_label": "Country", # y-axis categories
                "plot": {
                    "order_direction": "desc",
                    "orientation": "hbar",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": False,
                    "legend_outside": False,
                    "legend_labels": {
                        "operational": "Completed",
                        "under construction": "Under construction",
                        "announced": "Announced"
                    },
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "EUR",
                    "format_x_millions": True,
                    "currency_prefix": ""
                },
                "charts": [
                    {"lv1": "ALL", "lv2": "ALL",         "title": "",        "filename": "a.png"},
 
                ]
            },
                        {
                "name": "capacities_by_status_country",
                "output_dir": str(output_dir / "VF"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "product_lv1", "legend_title":"Technology" },
                "filters": { "status": [ "announced", "under construction", "operational"], "product_lv1": ["vehicle", "solar", "battery"],"product_lv2": ["ingot_wafer", "cell", "electric"] },
                "index_by": ["iso2"], 
                "index_label": "Country",  # y-axis categories
                "plot": {
                    # "order_on_stack_value": ["operational", "under construction"],
                    "order_direction": "desc",
                    "orientation": "hbar",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": False,
                    "legend_outside": False,
                                        "legend_labels": {
                        "operational": "Completed",
                        "under construction": "Under construction",
                        "announced": "Announced"
                    },
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "EUR",
                    "format_x_millions": True,
                    "currency_prefix": ""
                },
                "charts": [
                    {"lv1": "ALL", "lv2": "ALL",         "title": "",        "filename": "b.png"},
 
                ]
            },
                           {
                "name": "capacities_by_status_country",
                "output_dir": str(output_dir / "VF"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "regionHQ", "legend_title":"Headquarters" },
                "filters": { "status": [ "announced", "under construction", "operational"], "product_lv1": ["vehicle", "battery", "solar"],"product_lv2": ["ingot_wafer","cell", "electric"] },
                "index_by": ["iso2"], 
                "index_label": "Country",  # y-axis categories
                "plot": {
                    # "order_on_stack_value": ["operational", "under construction"],
                    "order_direction": "desc",
                    "orientation": "hbar",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": False,
                    "legend_outside": False,
                                        "legend_labels": {
                        "operational": "Announced",
                        "under construction": "Under construction",
                        "announced": "Completed"
                    },
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "EUR",
                    "format_x_millions": True,
                    "currency_prefix": ""
                },
                "charts": [
                    {"lv1": "ALL", "lv2": "ALL",         "title": "",        "filename": "c.png"},
 
                ]
            },
            {
                "name": "capacities_by_status_HQ",
                "output_dir": str(output_dir / "VF"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "regionHQ", "legend_title":"Headquarters" },
                "filters": { "status": [ "operational", "under construction", "announced"], "product_lv1": ["vehicle", "solar", "battery"],"product_lv2": ["ingot_wafer", "cell", "electric"] },            
                "index_by": ["iso2"],
                "index_label": "Country",   # y-axis categories
                "plot": {
                    "order_direction": "desc",
                    "show_value_labels": False,
                    "top_n": None,
                    "orientation": "hbar",
                    "normalize": False,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "EUR",
                    "format_x_millions": True,
                    "currency_prefix": "",
                    "x_unit": "EUR"
                },
                "charts": [
                    {"lv1": "ALL", "lv2": "ALL",         "title": "",        "filename": "d.png"}
                    # {"lv1": "battery", "lv2": "module_pack",  "title": "Battery modules/packs by status and HQ","filename": "battery_modules_status_HQ.png"},
                    # {"lv1": "solar",   "lv2": "cell",         "title": "Solar cells by status and HQ",          "filename": "solar_cells_status_HQ.png"},
                    # {"lv1": "solar",   "lv2": "polysilicon",  "title": "Solar polysilicon by status and HQ",    "filename": "solar_polysilicon_status_HQ.png"},
                    # {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Solar ingot-wafers by status and HQ",   "filename": "solar_ingot_wafer_status_HQ.png"},
                    # {"lv1": "vehicle", "lv2": "electric",     "title": "Electric vehicles by status and HQ",    "filename": "electric_vehicles_status_HQ.png"}
                ]
            },
            {
                "name": "investments_construction_operational_HQ_country",
                "output_dir": str(output_dir / "VF"),
                "value_col": "capacity",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "status", "legend_title":"Status"},
                "filters": { "status": [ "under construction", "operational", "announced"] },
                "index_by": ["regionHQ"],  # y-axis categories
                "index_label": "Headquarters",
                "plot": {
                    "order_by": "total_desc",
                    "top_n": None,
                    "normalize": False,
                    "orientation": "hbar",
                    "show_value_labels": False,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "Capacity (GWh)",
                    
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "",        "filename": "h.png"}
                    # {"lv1": "battery", "lv2": "module_pack",  "title": "Capacity - Battery modules/packs (under construction and operational) by country and HQ","filename": "capacity_battery_modules_country_HQ.png"},
                    # {"lv1": "solar",   "lv2": "cell",         "title": "Capacity - Solar cells by status (under construction and operational) by country and HQ",          "filename": "capacity_solar_country_HQ.png"},
                    # {"lv1": "solar",   "lv2": "polysilicon",  "title": "Capacity - Solar polysilicon (under construction and operational) by country and HQ",    "filename": "capacity_solar_polysilicon_countryHQ.png"},
                    # {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Capacity - Solar ingot-wafers(under construction and operational) by country and HQ",   "filename": "capacity_solar_ingot_wafer_country_HQ.png"},
                    # {"lv1": "vehicle", "lv2": "electric",     "title": "Capacity - Electric vehicles (under construction and operational) by country and HQ",    "filename": "capacity_electric_vehicles_country_HQ.png"}
                ]
            },
            {
                "name": "investments_construction_operational_HQ_country",
                "output_dir": str(output_dir / "HQ"),
                "value_col": "capacity",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "regionHQ" },
                "filters": { "status": [ "announced", "under construction", "operational"] },
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
                "stack": { "column": "status", "order": ["operational", "under construction", "announced"] },
                "filters": { "status": [ "announced", "under construction", "operational"] },
                "index_by": ["master"],  # y-axis categories
                "plot": {
                    "order_on_stack_value": ["operational", "under construction"],
                    "order_direction": "desc",
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
                    {"lv1": "battery", "lv2": "cell",         "title": "Capacity - Battery cells by company and status",        "filename": "capacity_battery_cells_company_status.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Capacity - Battery modules/packs by company and status","filename": "capacity_battery_modules_company_status.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Capacity - Solar cells by status by company and status",          "filename": "capacity_solar_company_status.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Capacity - Solar polysilicon by company and status",    "filename": "capacity_solar_polysilicon_company_status.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Capacity - Solar ingot-wafers by company and status",   "filename": "capacity_solar_ingot_wafer_company_status.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Capacity -Electric vehicles by company and status",    "filename": "capacity_electric_vehicles_announced_company_status.png"}
                ]
            },
            {
                "name": "capacity_company_iso_under_construction_operational",
                "output_dir": str(output_dir / "VF"),
                "value_col": "capacity",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "iso2",  "legend_title":"Country" },
                "filters": { "status": [ "under construction", "operational"] },
                "index_by": ["master"],  # y-axis categories
                "index_label": "Company",
                "plot": {
                    "order_by": "total_desc",
                    "orientation": "hbar",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": False,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "Capacity (units)"
                },
                "charts": [
                    # {"lv1": "battery", "lv2": "cell",         "title": "Capacity - Battery cells under construction and operational by company and country",        "filename": "capacity_battery_cells_construction_operational_company_country.png"},
                    # {"lv1": "battery", "lv2": "module_pack",  "title": "Capacity - Battery modules/packs  under consutuction and operational by company and country","filename": "capacity_battery_modules_construction_operational_company_country.png"},
                    # {"lv1": "solar",   "lv2": "cell",         "title": "Capacity - Solar cells under consutuction and operational by company and country",          "filename": "capacity_solar_announced_construction_operational_company_country.png"},
                    # {"lv1": "solar",   "lv2": "polysilicon",  "title": "Capacity -- Solar polysilicon  under consutuction and operational by company and country",    "filename": "capacity_solar_polysilicon_construction_operational_company_country.png"},
                    # {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Capacity - Solar ingot-wafers under consutuction and operational by company and country",   "filename": "capacity_solar_ingot_wafer_construction_operational_company_country.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "",    "filename": "e.png"}
                ]
            },
            {
                "name": "capacity_company_iso_under_construction_operational",
                "output_dir": str(output_dir / "COMPANY"),
                "value_col": "capacity",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "master" },
                "filters": { "status": [ "under construction", "operational"] },
                "index_by": ["iso2"],  # y-axis categories
                "plot": {
                    "order_by": "total_desc",
                    "orientation": "hbar",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": True,
                    "legend_outside": True,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "Capacity (units)"
                },
                "charts": [
                    {"lv1": "battery", "lv2": "cell",         "title": "Capacity - Battery cells under consutuction and operational by company and country",        "filename": "capacity_battery_cells_construction_operational_country_company.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Capacity - Battery modules/packs  under consutuction and operational by company and country","filename": "capacity_battery_modules_construction_operational_country_company.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Capacity - Solar cells under consutuction and operational by company and country",          "filename": "capacity_solar_announced_construction_operational_country_company.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Capacity -- Solar polysilicon  under consutuction and operational by company and country",    "filename": "capacity_solar_polysilicon_construction_operational_country_company.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Capacity - Solar ingot-wafers under consutuction and operational by company and country",   "filename": "capacity_solar_ingot_wafer_construction_operational_country_company.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Capacity --Electric vehicles under consutuction and operational by company and country",    "filename": "capacity_electric_vehicles_construction_operational_country_company.png"}
                ]
            },
            {
                "name": "capacity_company_iso_under_construction_operational",
                "output_dir": str(output_dir / "VF"),
                "value_col": "capacity",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "iso2", "legend_title":"Country" },
                "filters": { "status": [ "announced", "under construction", "operational"], "product_lv1": ["vehicle", "solar", "battery"],"product_lv2": ["ingot_wafer", "cell", "electric"] },
                "index_by": ["master"],  # y-axis categories
                "index_label": "Company",
                "plot": {
                    "order_by": "total_desc",
                    "orientation": "hbar",
                    "top_n": None,
                    "normalize": False,
                    "show_value_labels": False,
                    "legend_outside": False,
                    "legend_ncol": 2,
                    "dpi": 300,
                    "figsize": [11, 7],
                    "x_unit": "Capacity (units)"
                },
                "charts": [
                    {"lv1": "vehicle", "lv2": "electric",         "title": "",        "filename": "g.png"}
                    # {"lv1": "battery", "lv2": "module_pack",  "title": "Capacity - Battery modules/packs announced  by company and country","filename": "capacity_battery_modules_announced_company_country.png"},
                    # {"lv1": "solar",   "lv2": "cell",         "title": "Capacity - Solar cells announced  by company and country",          "filename": "capacity_solar_announced_announced_company_country.png"},
                    # {"lv1": "solar",   "lv2": "polysilicon",  "title": "Capacity -- Solar polysilicon announced by company and country",    "filename": "capacity_solar_polysilicon_announced_company_country.png"},
                    # {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Capacity - Solar ingot-wafers announced  by company and country",   "filename": "capacity_solar_ingot_wafer_announced_company_country.png"},
                    # {"lv1": "vehicle", "lv2": "electric",     "title": "Capacity --Electric vehicles announced by company and country",    "filename": "capacity_electric_vehicle_announced_company_country.png"}
                ]
            },
    # Capacity quarter plots ----------
                            {
                "name": "capacity_quarter_announced",
                "output_dir": str(output_dir / "QUARTER"),
                "value_col": "capacity",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "status" },
                "filters": {"status": [ "under construction", "operational",  "announced"] },
                "index_by": ["announced_on_quarter"],  # y-axis categories
                "plot": {
                    "orientation": "vbar",
                    "order_on_stack_value": ["operational", "under construction"],
                    "order_direction": "desc",
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
                "stack": { "column": "status" },
                "filters": {"status": [ "under construction", "operational"] },
                "index_by": ["announced_on_quarter"],  # y-axis categories
                "plot": {
                    "orientation": "vbar",
                    "order_on_stack_value": ["operational", "under construction"],
                    "order_direction": "desc",
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
                "name": "capacities_by_status_country",
                "output_dir": str(output_dir / "COUNTRY"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "status", "order": ["operational", "under construction", "announced"] },
                "filters": { "status": ["announced", "under construction", "operational"] },
                "index_by": ["iso2"],  # y-axis categories
                "plot": {
                    "order_on_stack_value": ["operational", "under construction"],
                    "order_direction": "desc",
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
                    {"lv1": "battery", "lv2": "cell",         "title": "Investment - Battery cells by status and country",        "filename": "investment_battery_cells_status_country.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Investment - Battery modules/packs by status and country","filename": "investment_battery_modules_status_country.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Investment - Solar cells by status and country",          "filename": "investment_solar_cells_status_country.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Investment - Solar polysilicon by status and country",    "filename": "investment_solar_polysilicon_status_country.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Investment - Solar ingot-wafers by status and country",   "filename": "investment_solar_ingot_wafer_status_country.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Investment - Electric vehicles by status and country",    "filename": "investment_electric_vehicles_status_country.png"}
                ]
            },
            {
                "name": "investments_by_status_country",
                "output_dir": str(output_dir / "COMPANY"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "status", "order": ["operational", "under construction", "announced"] },
                "filters": { "status": ["announced", "under construction", "operational"] },
                "index_by": ["iso2"],  # y-axis categories
                "plot": {
                    "order_on_stack_value": ["operational", "under construction"],
                    "order_direction": "desc",
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
                "stack": { "column": "status", "order": ["operational", "under construction", "announced"] },
                "filters": { "status": ["announced", "under construction", "operational"] },
                "index_by": ["regionHQ"],  # y-axis categories
                "plot": {
                    "order_on_stack_value": ["operational", "under construction"],
                    "order_direction": "desc",
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
                "filters": { "status": [ "announced", "under construction", "operational"] },
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
                "stack": { "column": "status", "order": ["operational", "under construction", "announced"] },
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
                "name": "investments_company_country_under_construction_operational",
                "output_dir": str(output_dir / "COMPANY"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "master" },
                "filters": { "status": [ "under construction", "operational"] },
                "index_by": ["iso2"],  # y-axis categories
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
                    {"lv1": "battery", "lv2": "cell",         "title": "Investment - Battery cells under consutuction and operational by company and country",        "filename": "investment_battery_cells_construction_operational_country_company.png"},
                    {"lv1": "battery", "lv2": "module_pack",  "title": "Investment- Battery modules/packs  under consutuction and operational by company and country","filename": "investment_battery_modules_construction_operational_country_company.png"},
                    {"lv1": "solar",   "lv2": "cell",         "title": "Investment - Solar cells under consutuction and operational by company and country",          "filename": "investment_solar_announced_construction_operational_country_company.png"},
                    {"lv1": "solar",   "lv2": "polysilicon",  "title": "Investment - Solar polysilicon  under consutuction and operational by company and country",    "filename": "investment_solar_polysilicon_construction_operational_country_company.png"},
                    {"lv1": "solar",   "lv2": "ingot_wafer",  "title": "Investment - Solar ingot-wafers under consutuction and operational by company and country",   "filename": "investment_solar_ingot_wafer_construction_operational_country_company.png"},
                    {"lv1": "vehicle", "lv2": "electric",     "title": "Investment -Electric vehicles under consutuction and operational by company and country",    "filename": "investment_electric_vehicles_construction_operational_country_company.png"}
                ]
            },
            {
                "name": "investments_company_country_announced",
                "output_dir": str(output_dir / "COMPANY"),
                "value_col": "investment",
                # stack on status (uses global STATUS_ORDER/COLORS if available)
                "stack": { "column": "iso2" },
                "filters": { "status": [ "announced", "under construction", "operational"] },
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
                "stack": { "column": "status" },
                "filters": {"status": [ "announced", "under construction", "operational"] },
                "index_by": ["announced_on_quarter"],  # y-axis categories
                "plot": {
                    "orientation": "vbar",
                    "order_on_stack_value": ["operational", "under construction"],
                    "order_direction": "desc",
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
                "stack": { "column": "status" },
                "filters": {"status": [ "under construction", "operational"] },
                "index_by": ["announced_on_quarter"],  # y-axis categories
                "plot": {
                    "orientation": "vbar",
                    "order_on_stack_value": ["operational", "under construction"],
                    "order_direction": "desc",
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
                "filters": { "status": [ "under construction", "operational"] ,  "product_lv1": ["battery", "vehicle", "solar"]},
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
            },
            {
                "name": "investment_quarter_by_productlv1_construction_operational",
                "output_dir": str(output_dir / "QUARTER"),
                "value_col": "investment",
                "stack": { "column": "product_lv1" },
                "filters": { "status": [ "announced", "under construction", "operational"] ,  "product_lv1": ["battery", "vehicle", "solar"],  "product_lv1": ["ingot_wafer", "cell", "module_pack", "electric"]},
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
                    {"lv1": "ALL", "lv2": "ALL", "title": "Investment by quarter (stacked by product level 1)", "filename": "investment_quarter_stack_lv1.png"}
                ]
            }

        ]
    }
    output_plots_from_config(df_merged, CONFIG)


if __name__ == "__main__":
    output_plots()

# -----------------------------
# Imports & constants
# -----------------------------
# from __future__ import annotations

# import os
# from typing import Dict, List, Tuple

# import sys; sys.path.append("..")

# import pandas as pd
# import matplotlib.pyplot as plt
# import numpy as np
# from pathlib import Path
# from typing import Any, Union

# # from mongo_client import facilities_collection
# from src.config import CAPACITIES_PLOT

# # mongo_client_setup.py
# import os
# import certifi
# from pymongo import MongoClient
# from pymongo.server_api import ServerApi
# from dotenv import load_dotenv
# import logging

# load_dotenv()

# MONGO_URI = os.getenv("MONGO_URI")
# DB_NAME = os.getenv("MONGO_DB_NAME")
# ARTICLES_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME")
# FACILITIES_COLLECTION = "facilities_develop" #os.getenv("MONGO_FACILITIES_COLLECTION") change later


# if not all([MONGO_URI, DB_NAME, ARTICLES_COLLECTION_NAME]):
#     raise RuntimeError("❌ Missing required MongoDB environment variables.")

# mongo_client = MongoClient(MONGO_URI, server_api=ServerApi('1'), tlsCAFile=certifi.where())
# db = mongo_client[DB_NAME]
# articles_collection = db[ARTICLES_COLLECTION_NAME]
# facilities_collection = db[FACILITIES_COLLECTION]
# geonames_collection = db["geonames_store"]

# #geonames_collection = db["geonames_lookup"]

# def test_mongo_connection():
#     try:
#         mongo_client.admin.command("ping")
#         print("✅ Connected to MongoDB Atlas!")
#     except Exception as e:
#         print(f"❌ MongoDB Connection Error: {e}")
#         raise

# # -------------------------------------------------
# # Config
# # -------------------------------------------------
# FIG_DIR = "storage/figures"

# # Order and colors for STATUS
# STATUS_ORDER: List[str] = ["operational", "under construction", "announced"]
# STATUS_COLORS: Dict[str, str] = {
#     "operational": "#8B0000",        # dark red
#     "under construction": "#FFA07A", # light salmon (faded orange/red)
#     "announced": "#7f7f7f",       # grey
# }

# # -----------------------------
# # LV2 -> LV1 backstop mapping
# # -----------------------------
# LV2_TO_LV1 = {
#     "module_pack": "battery",
#     "ingot_wafer": "solar",
#     "polysilicon": "solar",
#     "electric": "vehicles",
# }

# # -------------------------------------------------
# # Load
# # -------------------------------------------------
# def load_facility_df():
#     pipeline = [
#         {"$project": {
#             "_id": 0,
#             "owner": "$inst_canon",
#             "iso2": 1, "adm1": 1,
#             "product_lv1": 1, "product_lv2": 1,
#             "status": "$main.status",
#             "capacity": "$main.capacity",
#             "investment":"$main.investment",
#             "announced_on": "$main.announced_on",
#             "under_construction_on": "$main.under_construction_on",
#             "operational_on": "$main.operational_on"
#         }}
#     ]
#     rows = list(facilities_collection.aggregate(pipeline))
#     df = pd.DataFrame(rows)

#     # ensure product_lv2 is a scalar (explode lists)
#     df["product_lv2"] = df["product_lv2"].apply(lambda x: x if isinstance(x, list) else ([x] if x is not None else [pd.NA]))
#     df = df.explode("product_lv2", ignore_index=True)

#     # dates
#     date_cols = ["announced_on", "under_construction_on", "operational_on"]
#     for c in date_cols:
#         if c in df.columns:
#             df[c] = pd.to_datetime(df[c], errors="coerce")

#     # coerce capacities if objects slipped in
#     for c in ["capacity", "investment"]:
#         if c in df.columns and df[c].dtype == "object":
#             df[c] = pd.to_numeric(df[c], errors="coerce")

#     # optional export of the flat table you had before
#     output_cols = [
#         "iso2","adm1","owner","product_lv1","product_lv2","status","capacity","investment"
#         "announced_on","under_construction_on","operational_on",
#     ]
#     df.to_excel(CAPACITIES_PLOT, columns=[c for c in output_cols if c in df.columns], index=False)

#     return df

# # -----------------------------
# # Helpers
# # -----------------------------
# def _mk_lv1_lv2(sr_lv1: pd.Series, sr_lv2: pd.Series, *, debug: bool = True) -> pd.Series:
#     if debug:
#         print("[_mk_lv1_lv2] incoming lv1 dtype:", getattr(sr_lv1, "dtype", None))
#         print("[_mk_lv1_lv2] incoming lv2 dtype:", getattr(sr_lv2, "dtype", None))
#         try:
#             print("[_mk_lv1_lv2] sample lv1:", sr_lv1.astype("string").head(5).tolist())
#             print("[_mk_lv1_lv2] sample lv2:", sr_lv2.astype("string").head(5).tolist())
#         except Exception as e:
#             print("[_mk_lv1_lv2] (warn) failed showing samples:", e)

#     a = sr_lv1.astype("string").str.strip().str.lower().fillna("unknown")
#     b = sr_lv2.astype("string").str.strip().str.lower().fillna("unknown")
#     combined = a.str.replace(r"\s+", "_", regex=True) + "_" + b.str.replace(r"\s+", "_", regex=True)
#     if debug:
#         print("[_mk_lv1_lv2] combined sample:", combined.head(5).tolist())
#     return combined


# def summarize_extremes(
#     df_rows: pd.DataFrame,
#     *,
#     cap_col: str = "capacity",
#     status_col: str = "status",
#     method: str = "iqr",           # "iqr" | "quantile" | "topn"
#     param: float | int = 1.5,      # iqr: 1.5; quantile: 0.95; topn: 20
# ) -> Dict[str, Any]:
#     rows = df_rows.copy()
#     rows[cap_col] = pd.to_numeric(rows[cap_col], errors="coerce")
#     rows = rows[pd.notna(rows[cap_col]) & (rows[cap_col] > 0)]

#     if rows.empty:
#         return {
#             "threshold": float("nan"),
#             "extreme_rows": rows.iloc[0:0].copy(),
#             "by_status": pd.DataFrame(columns=[status_col, "sum_capacity"]).set_index(status_col),
#             "overall": pd.DataFrame([{"n_extreme": 0, "sum_capacity": 0.0}]),
#         }

#     if method == "iqr":
#         q1, q3 = rows[cap_col].quantile([0.25, 0.75])
#         iqr = q3 - q1
#         thr = q3 + float(param) * iqr
#     elif method == "quantile":
#         thr = float(rows[cap_col].quantile(float(param)))
#     elif method == "topn":
#         n = int(param)
#         thr = rows[cap_col].nlargest(n).min()
#     else:
#         raise ValueError("Unknown method for extremes")

#     extreme_rows = rows.loc[rows[cap_col] >= thr].copy().sort_values(cap_col, ascending=False)
#     by_status = (
#         extreme_rows.groupby(status_col, dropna=False)[cap_col]
#         .sum(min_count=1)
#         .rename("sum_capacity")
#         .to_frame()
#         .sort_values("sum_capacity", ascending=False)
#     )
#     overall = pd.DataFrame([{
#         "n_extreme": int(len(extreme_rows)),
#         "sum_capacity": float(extreme_rows[cap_col].sum())
#     }])

#     return {
#         "threshold": float(thr),
#         "extreme_rows": extreme_rows,
#         "by_status": by_status,
#         "overall": overall,
#     }

# # -----------------------------
# # Main plotting function
# # -----------------------------


# def plot_status_ratio_bars_lv2(
#     df: pd.DataFrame,
#     *,
#     demand: Dict[str, float],                     # demand per parent lv1 (e.g., "battery", "solar", "vehicles")
#     outfile_png: str,
#     include_lv2: List[str] = ("cell", "module_pack", "ingot_wafer", "polysilicon", "electric"),
#     status_filter: List[str] = ("operational", "under construction", "announced"),
#     title: str = "Capacity / Demand by LV2 and status (side-by-side bars)",
#     figsize: Tuple[int, int] = (12, 7),
#     dpi: int = 300,
#     debug: bool = True,
#     return_dfs: bool = True,
#     extreme_method: str = "iqr",
#     extreme_param: float | int = 1.5,
# ):
#     """
#     Grouped bar chart of (capacity / demand) for each status, per lv1_lv2 tech.
#     - One bar per status (side-by-side).
#     - Numbers on bars in percent.
#     - Returns (main_df_ratios, group_preview, extremes_overall, extremes_by_status, extreme_rows)
#     """
#     # 1) Filter rows
#     sub = df[df["status"].isin(status_filter)].copy()
#     include_lv2_lower = {s.lower() for s in include_lv2}
#     sub["product_lv2"] = sub["product_lv2"].astype("string").str.strip().str.lower()
#     sub = sub[sub["product_lv2"].isin(include_lv2_lower)]

#     # 2) Normalize lv1 + build lv1_lv2
#     sub["product_lv1"] = sub["product_lv1"].astype("string").str.strip().str.lower()
#     sub["lv1_lv2"] = (
#         sub["product_lv1"].str.replace(r"\s+", "_", regex=True).fillna("unknown")
#         + "_"
#         + sub["product_lv2"].str.replace(r"\s+", "_", regex=True).fillna("unknown")
#     )

#     # 3) Robust parent_lv1 (fallback via LV2_TO_LV1 if missing or not in demand keys)
#     demand_keys = pd.Index([str(k).lower().strip() for k in demand.keys()])
#     sub["parent_lv1"] = sub["product_lv1"]
#     mask_missing = sub["parent_lv1"].isna() | sub["parent_lv1"].isin(["", "unknown", "nan", "none"])
#     mask_not_in_demand = ~sub["parent_lv1"].isin(demand_keys)
#     fix_mask = mask_missing | mask_not_in_demand
#     sub.loc[fix_mask, "parent_lv1"] = sub.loc[fix_mask, "product_lv2"].map(LV2_TO_LV1)
#     sub["parent_lv1"] = sub["parent_lv1"].astype("string").str.strip().str.lower()

#     # 4) Numeric capacity
#     sub["capacity"] = pd.to_numeric(sub["capacity"], errors="coerce")

#     # 5) Aggregate absolute capacity by (lv1_lv2, status)
#     g_abs = (
#         sub.groupby(["lv1_lv2", "status"], dropna=False)["capacity"]
#         .sum(min_count=1, numeric_only=True)
#         .unstack("status")
#         .reindex(columns=STATUS_ORDER, fill_value=0.0)
#         .fillna(0.0)
#     )
#     if g_abs.empty:
#         print("[plot_status_ratio_bars_lv2] No data after filtering.")
#         return None

#     # 6) Map demand
#     parent_map = (
#         sub.dropna(subset=["lv1_lv2", "parent_lv1"])
#            .drop_duplicates("lv1_lv2")
#            .set_index("lv1_lv2")["parent_lv1"]
#     )
#     demand_series = (
#         g_abs.index.to_series()
#             .map(parent_map)
#             .map(lambda k: float(demand.get(str(k), np.nan)))
#     )

#     # 7) Compute ratios
#     g_rat = g_abs.copy()
#     denom = demand_series.replace(0, np.nan)

#     for s in STATUS_ORDER:
#         g_rat[f"{s}_abs_capacity"] = g_abs[s]
#         g_rat[f"{s}_ratio_to_demand"] = g_abs[s] / denom

#     g_rat["__demand__"] = demand_series
#     g_rat["total_abs_capacity"] = g_abs[STATUS_ORDER].sum(axis=1)
#     g_rat["total_ratio"] = g_rat["total_abs_capacity"] / denom

#     # 8) Sort
#     order = g_rat["total_ratio"].replace([np.inf, -np.inf], np.nan).sort_values(ascending=False).index
#     g_rat = g_rat.loc[order]

#     # 9) Plot ratios (converted to %)
#     os.makedirs(os.path.dirname(outfile_png), exist_ok=True)
#     colors = [STATUS_COLORS.get(s, "#cccccc") for s in STATUS_ORDER]

#     ratio_cols = [f"{s}_ratio_to_demand" for s in STATUS_ORDER]
#     g_plot = g_rat[ratio_cols].replace([np.inf, -np.inf], np.nan).fillna(0.0)
#     g_plot.columns = STATUS_ORDER
#     g_plot_pct = g_plot * 100

#     ax = g_plot_pct.plot(kind="barh", stacked=True, figsize=figsize, color=colors)
#     ax.set_title(title)
#     ax.set_xlabel("")
#     ax.set_ylabel("")
#     ax.legend(STATUS_ORDER, title="Status", frameon=False, bbox_to_anchor=(1.0, 0.5), loc="center left")

#     import matplotlib.ticker as mtick
#     ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=100))

#     custom_labels = {
#         "battery_cell": "Battery cells",
#         "vehicle_electric": "Electric vehicles",
#         "solar_cell": "Solar cells",
#         "solar_ingot_wafer": "Solar ingots and wafers",
#     }
#     ax.set_yticklabels([custom_labels.get(lbl, lbl) for lbl in g_plot.index])

#     # # Labels on bars
#     # min_dx = 10  # percent separation
#     # labels_by_row = {}

#     # for patch in ax.patches:
#     #     width = patch.get_width()
#     #     if not (np.isfinite(width) and width > 0):
#     #         continue
#     #     row_y = patch.get_y() + patch.get_height() / 2.0
#     #     x = patch.get_x() + width
#     #     if row_y not in labels_by_row:
#     #         labels_by_row[row_y] = []
#     #     if any(abs(x - x0) < min_dx for (x0, _) in labels_by_row[row_y]):
#     #         continue
#     #     ax.text(x, row_y, f"{width:.0f}%", va="center", ha="left", fontsize=8)
#     #     labels_by_row[row_y].append((x, row_y))

#     plt.tight_layout(rect=[0, 0, 0.82, 1])
#     plt.savefig(outfile_png, dpi=dpi, bbox_inches="tight")
#     plt.close()

#     # 10) Extremes
#     extremes = summarize_extremes(
#         sub[["owner","iso2","adm1","product_lv1","product_lv2","status","capacity"]],
#         cap_col="capacity", status_col="status",
#         method=extreme_method, param=extreme_param
#     )

#     # 11) Group preview
#     group_preview = (
#         sub[["owner","iso2","adm1","product_lv1","product_lv2","parent_lv1","lv1_lv2","status","capacity"]]
#         .sort_values(["lv1_lv2","status"])
#         .reset_index(drop=True)
#     )

#     if debug:
#         print("[parent_lv1 mapping] sample:\n", group_preview[["lv1_lv2","parent_lv1"]].drop_duplicates().head(10))
#         print("[group_preview] sample:\n", group_preview.head(10))

#     if return_dfs:
#         return g_rat, group_preview, extremes["overall"], extremes["by_status"], extremes["extreme_rows"]
#     return None


# # -----------------------------
# # Example usage
# # -----------------------------

# if __name__ == "__main__":
#     demand = {
#         "battery": 410,          # GWh
#         "solar": 58,             # GW
#         "vehicles": 2300000,     # units
#     }

#     output_dir = Path("storage")
#     comp_dir = output_dir / "figures"/ "VF"
#     comp_dir.mkdir(parents=True, exist_ok=True)

#     base_dir = Path.cwd()
#     input_file = base_dir / "storage" / "input" / "unique_owners_filled.xlsx"

#     df_owner = pd.read_excel(input_file)
#     df_merged = load_facility_df()

#     # Ratios per status (side-by-side) with numbers on bars; keep group preview & extremes
#     main_df, group_preview, extremes_overall, extremes_by_status, extreme_rows = plot_status_ratio_bars_lv2(
#         df=df_merged,
#         demand=demand,
#         outfile_png=str(comp_dir / "capacity_by_lv2_status_ratios_grouped_new.png"),
#         include_lv2=["cell", "ingot_wafer",  "electric"],
#         status_filter=["operational", "under construction", "announced"],
#         title="",
#         return_dfs=True,
#         extreme_method="iqr",
#         extreme_param=1.5,
#     )

#     # Ready for Jupyter use
#     print("\n[main_df head — with demand, capacities, and ratios]")
#     cols_to_show = (
#         ["__demand__"] +
#         [c for c in main_df.columns if c.endswith("_abs_capacity")] +
#         [c for c in main_df.columns if c.endswith("_ratio_to_demand")] +
#         ["total_abs_capacity", "total_ratio"]
#     )
#     print(main_df[cols_to_show].head())

#     print("\n[group_preview head]")
#     print(group_preview.head(20))

#     print("\n[extremes_overall]")
#     print(extremes_overall)

#     print("\n[extremes_by_status]")
#     print(extremes_by_status)

#     print("\n[extreme_rows sample]")
#     print(extreme_rows.head())

#     numerator_cols = [c for c in main_df.columns if c.endswith("_abs_capacity")] + ["total_abs_capacity"]
#     print("\n[NUMERATORS — capacities by status (the share numerators)]")
#     print(main_df[numerator_cols])

#     # Optional: export to CSV/Excel
#     main_df[numerator_cols].to_excel("storage/figures/VF/share_numerators.xlsx")




