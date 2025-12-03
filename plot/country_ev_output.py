import sys; sys.path.append("..")
import pandas as pd

df = pd.read_excel(
    "reconcile/storage/input/vehicles_impute.xlsx",
    sheet_name="EV-volumes",
    skiprows=1,
)

# Name of the country column
COUNTRY_COL = "Vehicle Production Country"

# === 1. Forward-fill countries (THIS is the key fix) ===
df[COUNTRY_COL] = df[COUNTRY_COL].ffill()

# === 2. Drop the grand total row ===
df = df[df[COUNTRY_COL] != "Grand Total"]

# === 3. Identify the year columns (2010–2024) ===
year_cols = [
    col for col in df.columns
    if isinstance(col, int) or (isinstance(col, str) and col.isdigit())
]

# === 4. Group by country and sum ===
country_sum = (
    df.groupby(COUNTRY_COL, as_index=False)[year_cols]
      .sum()
)

# === 5. Export ===
output_path = "vehicle_production_by_country.xlsx"
country_sum.to_excel(output_path, index=False)

print(f"Saved country production sums to: {output_path}")