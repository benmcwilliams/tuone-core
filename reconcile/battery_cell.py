import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# --- Read Excel ---
df = pd.read_excel("rhodium_cell.xlsx")

# --- Group European countries and bucket a few into "Other" ---
EUROPE = {
    "Austria","Belgium","Bulgaria","Croatia","Cyprus","Czechia","Czech Republic","Denmark","Estonia","Finland",
    "France","Germany","Greece","Hungary","Ireland","Italy","Latvia","Lithuania","Luxembourg","Malta","Netherlands",
    "Poland","Portugal","Romania","Slovakia","Slovenia","Spain","Sweden","Norway","Switzerland","United Kingdom"
}
OTHER = {"Japan", "Canada", "Taiwan", "India", "United States"}

df["region_temp"] = df["countryHQ"].apply(lambda x: "Europe" if x in EUROPE else x)
df["region"] = df["region_temp"].apply(lambda x: "Other" if x in OTHER else x)

# --- Aggregate total capacity by status × region ---
agg = (
    df.groupby(["status", "region"], dropna=False)["phase_capacity"]
      .sum()
      .reset_index()
      .rename(columns={"phase_capacity": "total_capacity"})
)

# --- Pivot and order (Operational on top) ---
status_order = ["announced", "under construction", "operational"]
pivot = agg.pivot(index="status", columns="region", values="total_capacity").fillna(0)
pivot = pivot.reindex(status_order)

# --- Column order: highlight China & South Korea; keep others after in stable order ---
preferred = ["China", "South Korea", "Europe", "Other"]
cols_order = [c for c in preferred if c in pivot.columns] + [c for c in pivot.columns if c not in preferred]
pivot = pivot[cols_order]

# --- Colors: highlight China, South Korea, and Europe; keep others softer ---
color_map = {
    "China": "#d62728",         # vivid red
    "South Korea": "#1f77b4",   # deep blue
    "Europe": "#9ecae1",        # strong green
    "Other": "#c7c7c7",         # light gray
}

# Apply in column order
colors = [color_map.get(c, "#dddddd") for c in cols_order]

# --- Plot horizontal stacked bars ---
fig, ax = plt.subplots(figsize=(10, 6))
pivot.plot(kind="barh", stacked=True, ax=ax, color=colors)

# Title + subtitle
fig.suptitle("European battery cell manufacturing capacity by operational status", fontsize=16, fontweight="bold")
ax.set_title("Stacks show where the responsible company have their HQ", fontsize=12)

# Axes & grid
ax.set_xlabel("Total capacity (GWh)", fontsize=12)
ax.set_ylabel("")
ax.grid(axis="x", linestyle="--", alpha=0.5)
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x):,}"))

# Legend
ax.legend(title="Region", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)

plt.tight_layout()
plt.show()