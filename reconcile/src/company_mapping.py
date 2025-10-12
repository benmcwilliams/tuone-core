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
    ("samsung sdi", "HU", "Budapest"): "Pest County",
    ("oxford pv", "GB", "Brandenburg an der Havel"): "Brandenburg",
    ("italvolt", "IT", "Scarmagno"): "Piedmont",
    ("mcpv", "NL", "Veendam Municipality"): "Groningen. Municipality",
    ("lg energy solution", "PL", "Kobierzyce"): "Wrocław",
    ("gotion inobat batteries", "SK", "Trnava Region"): "Nitra Region",
    ("svolt", "DE", "Heusweiler"): "Überherrn",
    ("svolt", "DE", "Saarland"): "Überherrn",
    # add more:
    # ("bmw", "DE", "Dingolfing-Landau"): "Dingolfing",
}

JV_MERGE = {
    # EXAMPLES:
    # ("acc battery JV", "DE", "Arnstadt", "battery"): "catl",
    # ("some JV", "FR", "Fos-sur-Mer", "recycling"): "carbon",
    ("stellantis", "ES", "Aragon", "battery"): "stellantis catl",
    ("volvo northvolt", "SE", "Gothenburg Municipality", "battery"): "volvo",
    ("northvolt", "SE", "Gothenburg Municipality", "battery"): "volvo",
    ("opel", "DE", "Kaiserslautern", "battery"): "automotive cell company",
    ("stellantis", "DE", "Kaiserslautern", "battery"): "automotive cell company",
    ("volkswagen northvolt", "DE", "Salzgitter", "battery"): "volkswagen",
    ("west midlands gigafactory", "GB", "Coventry", "battery"): "eve energy",
    ("chery", "ES", "Catalonia", "vehicle"): "chery ebro",
    ("ebro", "ES", "Catalonia", "vehicle"): "chery ebro",
    ("ford", "RO", "Dolj", "vehicle"): "ford otosan",
    ("psa group", "FR", "Mullhouse", "vehicle"): "stellantis",
}