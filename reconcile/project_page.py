import sys; sys.path.append("..")
import os
import pandas as pd
import matplotlib.pyplot as plt
from mongo_client import facilities_collection
from src.config import CAPACITIES_PLOT

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
            "announced_on": "$main.announced_on",
            "under_construction_on": "$main.under_construction_on",
            "operational_on": "$main.operational_on",
            "greenfield_status": "$greenfield.status",
            "greenfield_capacity": "$greenfield.capacity",
            "greenfield_announced_on": "$greenfield.announced_on",
            "greenfield_under_construction_on": "$greenfield.under_construction_on",
            "greenfield_operational_on": "$greenfield.operational_on",
        }}
    ]
    rows = list(facilities_collection.aggregate(pipeline))
    df = pd.DataFrame(rows)

    # ensure product_lv2 is a scalar (explode lists)
    df["product_lv2"] = df["product_lv2"].apply(lambda x: x if isinstance(x, list) else ([x] if x is not None else [pd.NA]))
    df = df.explode("product_lv2", ignore_index=True)

    # dates
    date_cols = [
        "announced_on", "under_construction_on", "operational_on",
        "greenfield_announced_on", "greenfield_under_construction_on", "greenfield_operational_on"
    ]
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    # coerce capacities if objects slipped in
    for c in ["capacity", "greenfield_capacity"]:
        if c in df.columns and df[c].dtype == "object":
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # optional export of the flat table you had before
    output_cols = [
        "iso2","adm1","owner","product_lv1","product_lv2","status","capacity",
        "announced_on","under_construction_on","operational_on",
        "greenfield_status","greenfield_capacity",
        "greenfield_announced_on","greenfield_under_construction_on","greenfield_operational_on"
    ]
    df.to_excel(CAPACITIES_PLOT, columns=[c for c in output_cols if c in df.columns], index=False)

    return df

def build_pivot(df: pd.DataFrame, lv1: str, lv2: str, value_col: str = "capacity") -> pd.DataFrame:
    sub = df[(df["product_lv1"] == lv1) & (df["product_lv2"] == lv2)].copy()
    if sub.empty:
        return pd.DataFrame()
    pivot = (
        sub.groupby(["iso2", "status"], dropna=False)[value_col]
           .sum(min_count=1, numeric_only=True)
           .reset_index()
           .pivot_table(index="iso2", columns="status", values=value_col, fill_value=0.0)
           .reindex(columns=STATUS_ORDER)  # add missing cols as NaN then fill below
           .fillna(0.0)
    )
    # Sort by operational desc then UC then announced
    sort_cols = [c for c in STATUS_ORDER if c in pivot.columns]
    if sort_cols:
        pivot = pivot.sort_values(by=sort_cols, ascending=[False]*len(sort_cols))
    return pivot

def plot_stacked_barh(pivot: pd.DataFrame, title: str, outfile: str):
    if pivot.empty:
        print(f"[skip] No data to plot for: {title}")
        return
    os.makedirs(os.path.dirname(outfile), exist_ok=True)

    ax = pivot.plot(
        kind="barh",
        stacked=True,
        figsize=(10, 6),
        color=[STATUS_COLORS.get(c, "#cccccc") for c in pivot.columns]
    )
    ax.set_xlabel("Capacity (product_lv2 defined units)")
    ax.set_ylabel("Country (iso2)")
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(outfile, dpi=300)
    plt.close()

def output_capacities_plot():
    df = load_facility_df()

    combos = [
        # (lv1, lv2, plot_title, filename)
        ("battery", "cell",         "Battery cell capacity by status and country",              f"{FIG_DIR}/battery_cells_plot.png"),
        ("battery", "module_pack",  "Battery packs/modules capacity by status and country",     f"{FIG_DIR}/battery_modules_plot.png"),
        ("solar", "cell",           "Solar cell capacity by status and country",                f"{FIG_DIR}/solar_cells_plot.png"),
        ("solar", "polysilicon",    "Solar polysilicon capacity by status and country",         f"{FIG_DIR}/solar_polysilicon_plot.png"),
        ("solar", "ingot_wafer",    "Solar ingot-wafer capacity by status and country",         f"{FIG_DIR}/solar_ingot_wafer_plot.png"),
    ]

    for lv1, lv2, title, path in combos:
        pivot = build_pivot(df, lv1, lv2, value_col="capacity")
        plot_stacked_barh(pivot, title, path)

if __name__ == "__main__":
    output_capacities_plot()