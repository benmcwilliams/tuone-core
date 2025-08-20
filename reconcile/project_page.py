import sys; sys.path.append("..")
import pandas as pd
from mongo_client import facilities_collection
from src.config import CAPACITIES_PLOT

def output_capacities_plot():

    pipeline = [
        {"$project": {
            "_id": 0,
            "owner": "$inst_canon",          # rename
            "iso2": 1,
            "adm1": 1,
            "product_lv1": 1,
            "product_lv2": 1,   
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

    # --- minimal: ensure list + explode
    df["product_lv2"] = df["product_lv2"].apply(lambda x: x if isinstance(x, list) else ([x] if x is not None else [pd.NA]))
    df = df.explode("product_lv2", ignore_index=True)

    # Optional: parse dates + make NaNs proper
    date_cols = ["announced_on", "under_construction_on", "operational_on",
        "greenfield_announced_on", "greenfield_under_construction_on", "greenfield_operational_on"]  # include operations
    for c in date_cols:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    # If capacity is sometimes stored as BSON Double NaN, pandas will already see it as np.nan
    # but if it was a dict (rare), coerce:
    if "greenfield_capacity" in df.columns and df["greenfield_capacity"].dtype == "object":
        df["greenfield_capacity"] = pd.to_numeric(df["greenfield_capacity"], errors="coerce")

    print(df.head())

    output_cols = ["iso2", "adm1", "owner", "product_lv1", "product_lv2", "status", "capacity", "announced_on", "under_construction_on",
                   "operational_on", "greenfield_status", "greenfield_capacity", "greenfield_announced_on", "greenfield_under_construction_on",
                   "greenfield_operational_on"]
    
    df.to_excel(CAPACITIES_PLOT, columns=output_cols, index=False)

    battery_cells = df[(df["product_lv1"] == "battery") & (df["product_lv2"] == "cell")].copy()

    battery_cells_plot = (
        battery_cells
        .groupby(["iso2", "status"])
        .sum(numeric_only=True)
        .reset_index()
        .copy()
        ).pivot_table(index="iso2",columns="status",values="capacity")

    status_order = ["operational", "under construction", "announced"]
    battery_cells_plot = battery_cells_plot.reindex(columns=status_order).sort_values(by="operational", ascending=False)


    import matplotlib.pyplot as plt

    # make a horizontal stacked bar chart
    ax = battery_cells_plot.plot(
        kind="barh",
        stacked=True,
        figsize=(10, 6),
        colormap="tab20"
    )

    ax.set_xlabel("Capacity (GWh)")
    ax.set_ylabel("Country (iso2)")
    ax.set_title("Battery cell manufacturing capacity by status and country")

    plt.tight_layout()
    plt.savefig("battery_cells_plot.png", dpi=300)
    plt.close()

if __name__ == "__main__":
    output_capacities_plot()