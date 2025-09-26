import sys; sys.path.append("..")
import json
import pandas as pd

# Load company mapping
with open('src/company_mapping.json', 'r') as f:
    company_mapping = json.load(f)

# Build reverse mapping
reverse_mapping = {}
for canonical, aliases in company_mapping.items():
    reverse_mapping[canonical.lower()] = canonical
    for alias in aliases:
        reverse_mapping[alias.lower()] = canonical

# Function to map to canonical
def map_to_canonical(name):
    if pd.isna(name):
        return name
    return reverse_mapping.get(str(name).lower(), name)

SITE_MERGE = {
    # collapse CATL’s nearby German sites to one admin key
    ("catl", "DE", "Erfurt"): "Arnstadt",     # Erfurt → Arnstadt
    ("tesla", "DE", "Berlin"): "Grünheide (Mark)",
    ("tesla", "DE", "Brandenburg"): "Grünheide (Mark)",
    ("carbon", "FR", "Marseille"): "Fos-sur-Mer",
    ("holosolis", "FR", "Sarreguemines"): "Hambach",
    ("samsung sdi", "HU", "Budapest"): "Pest County"
    # add more:
    # ("bmw", "DE", "Dingolfing-Landau"): "Dingolfing",
}