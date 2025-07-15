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