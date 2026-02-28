import sys; sys.path.append("..")
import json
import pandas as pd

# Load company mapping
with open('src/company_mapping.json', 'r', encoding='utf-8') as f:
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
    # germany
    ("catl", "DE", "Erfurt"): "Arnstadt",     # Erfurt → Arnstadt
    ("catl", "DE", "Thuringia"): "Arnstadt",
    ("tesla", "DE", "Berlin"): "Grünheide (Mark)",
    ("tesla", "DE", "Brandenburg"): "Grünheide (Mark)",
    ("svolt", "DE", "Heusweiler"): "Überherrn",
    ("svolt", "DE", "Saarland"): "Überherrn",
    ("porsche", "DE", "Kirchentellinsfurt"): "Reutlingen",
    ("valmet automotive", "DE", "Bad Friedrichshall"): "Kirchardt",
    ("meyer burger", "DE", "Bitterfeld-Wolfen"): "Thalheim",
    ("meyer burger", "DE", "Thalheim/Erzgeb."): "Thalheim",
    ("oxford pv", "DE", "Brandenburg an der Havel"): "Brandenburg",
    ("leclanche", "DE", "Baden-Wurttemberg"): "Willstätt",

    # france
    ("carbon", "FR", "Marseille"): "Fos-sur-Mer",
    ("holosolis", "FR", "Sarreguemines"): "Hambach",
    ("automotive cell company", "FR", "Billy-Berclau"): "Douvrin",

    # united kingdom
    ("oxford pv", "GB", "Brandenburg an der Havel"): "Brandenburg",
    ("bmw", "GB", "Swindon"): "Oxfordshire",
    ("oxford pv", "GB", "Brandenburg an der Havel"): "Brandenburg",
    ("vestas", "GB", "Newport"): "Isle of Wight",
    ("altilium metals", "GB", "Devon"): "Plymouth",

    # spain
    ("hyundai mobis", "ES", "Navarre"): "Pamplona",
    ("stellantis", "ES", "Figueruelas  Municipality"): "Zaragoza Municipality",
    ("atersa", "ES", "Almussafes"): "Valencia",
    ("stellantis catl", "ES", "Zaragoza Municipality"): "Figueruelas  Municipality",
    ("lm wind power", "ES", "Castellón de la Plana/Castelló de la Plana"): "Valencia",

    # hungary
    ("samsung sdi", "HU", "Budapest"): "Pest County",

    # italy
    ("italvolt", "IT", "Scarmagno"): "Piedmont",
    ("enel", "IT", "Sicily"): "Catania",
    ("futurasun", "IT", "Cittadella"): "Padova",
    ("midsummer", "IT", "Bari"): "Apulia",
    ("faam fib spa", "IT", "Caserta"): "Teverola",

    # netherlands
    ("mcpv", "NL", "Veendam Municipality"): "Groningen. Municipality",
    ("solarge", "NL", "Gemeente Weert"): "Eindhoven Municipality",

    # poland
    ("lg energy solution", "PL", "Kobierzyce"): "Wrocław",
    ("giga pv", "PL", "Silesia"): "Racibórz",
    ("capchem", "PL", "Wroclaw"): "Śrem",
    ("capchem", "PL", "Wrocław"): "Śrem",

    # other
    ("gotion inobat batteries", "SK", "Trnava Region"): "Nitra Region",
    # add more:
    # ("bmw", "DE", "Dingolfing-Landau"): "Dingolfing",
}

JV_MERGE = {
    # for cases at the same location, where we want to collapse one company or joint venture into another.
    # spain
    ("stellantis", "ES", "Aragon", "battery"): "stellantis catl",
    ("stellantis", "ES", "Zaragoza Municipality", "battery"): "stellantis catl",
    ("catl", "ES", "Zaragoza Municipality", "battery"): "stellantis catl",
    ("chery", "ES", "Catalonia", "vehicle"): "chery ebro",
    ("ebro", "ES", "Catalonia", "vehicle"): "chery ebro",
    ("chery", "ES", "Barcelona", "vehicle"): "chery ebro",
    ("ebro", "ES", "Barcelona", "vehicle"): "chery ebro",
    ("seat", "ES", "Navarre", "vehicle"): "volkswagen",
    ("volkswagen", "ES", "Catalonia", "vehicle"): "seat",
    ("cupra", "ES", "Catalonia", "vehicle"): "seat",

    # germany
    ("opel", "DE", "Kaiserslautern", "battery"): "automotive cell company",
    ("stellantis", "DE", "Kaiserslautern", "battery"): "automotive cell company",
    ("volkswagen northvolt", "DE", "Salzgitter", "battery"): "volkswagen",
    ("northvolt volkswagen", "DE", "Salzgitter", "battery"): "volkswagen",
    ("northvolt", "DE", "Salzgitter", "battery"): "volkswagen",
    ("vw northvolt", "DE", "Salzgitter", "battery"): "volkswagen",
    ("european battery union", "DE", "Salzgitter", "battery"): "volkswagen",
    ("northvolt", "DE", "Heide", "battery"): "lyten",
    ("daimler", "DE", "Kamenz", "battery"): "accumotive",
    ("mercedes benz", "DE", "Kamenz", "battery"): "accumotive",
    ("siemens", "DE", "Cuxhaven", "wind"): "siemens gamesa",
    ("pbt", "DE", "Hagen", "battery"): "pure battery technologies",
    ("seat", "DE", "Zwickau", "vehicle"): "volkswagen",
    ("skoda", "DE", "Zwickau", "vehicle"): "volkswagen",
    ("audi", "DE", "Zwickau", "vehicle"): "volkswagen",

    # france
    ("stellantis", "FR", "Douvrin", "battery"): "automotive cell company",
    ("psa group", "FR", "Mullhouse", "vehicle"): "stellantis",
    ("renault", "FR", "Douai", "battery"): "aesc",
    ("saft", "FR", "Nersac", "battery"): "automotive cell company",
    ("lm wind power", "FR", "Montoir-de-Bretagne", "wind"): "general electric",
    ("xtc new energy technology france", "FR", "Dunkerque", "battery"): "orano xtc new energy",

    # sweden
    ("volvo northvolt", "SE", "Gothenburg Municipality", "battery"): "volvo",
    ("northvolt", "SE", "Gothenburg Municipality", "battery"): "volvo",

    # uk
    ("west midlands gigafactory", "GB", "Coventry", "battery"): "eve energy",
    ("nissan", "GB", "Sunderland", "battery"): "aesc",
    ("tata motors", "GB", "Somserset", "battery"): "agratas",
    ("tata motors", "GB", "Somerset", "battery"): "agratas",
    ("envision", "GB", "Sunderland", "battery"): "aesc",
    ("nissan envision aesc", "GB", "Sunderland", "battery"): "aesc",
    ("nissan envision aesc", "GB", "Sunderland", "vehicle"): "nissan",
    ("siemens gamesa", "GB", "Kingston upon Hull", "wind"): "green port hull",
    ("siemens", "GB", "Kingston upon Hull", "wind"): "green port hull",
    ("siemens gamesa associated british ports", "GB", "Kingston upon Hull", "wind"): "green port hull",
    ("siemens", "GB", "Kingston upon Hull", "wind"): "green port hull",

    # poland
    ("northvolt", "PL", "Gdańsk", "battery"): "lyten",
    ("daimler", "PL", "Jawor", "battery"): "mercedes benz",
    ("fiat", "PL", "Tychy", "vehicle"): "stellantis",
    ("lm wind power", "PL", "Gmina Goleniów", "wind"): "vestas",
    ("leapmotor international", "PL", "Tychy", "vehicle"): "stellantis",

    # portugal
    ("senvion", "PT", "Aveiro", "wind"): "siemens gamesa",
    ("senvion", "PT", "Viseu", "wind"): "siemens gamesa",
    ("senvion se and senvion", "PT", "Aveiro", "wind"): "siemens gamesa",
    ("ria blades", "PT", "Aveiro", "wind"): "siemens gamesa",

    # denmark
    ("bonus energy", "DK", "Ålborg Kommune", "wind"): "siemens gamesa",
    ("siemens", "DK", "Ikast-Brande Kommune", "wind"): "siemens gamesa",

    # czechia
    ("volkswagen", "CZ", "Mladá Boleslav", "vehicle"): "skoda",
    ("toyota psa", "CZ", "Kolín", "vehicle"): "tmmcz",
    ("toyota motor", "CZ", "Kolín", "vehicle"): "tmmcz",

    # finland
    ("finnish minerals group epsilon advanced materials", "FI", "Vaasa", "battery"): "freyr",
    ("Finnish Battery Chemicals Oy", "FI", "Vaasa", "battery"): "epsilon advanced materials",

    # slovakia
    ("skoda", "SK", "Bratislava Region", "vehicle"): "volkswagen",
    ("audi", "SK", "Bratislava Region", "vehicle"): "volkswagen",
    ("porsche", "SK", "Bratislava Region", "vehicle"): "volkswagen",
    ("psa", "SK", "Trnava Region", "vehicle"): "stellantis",
    ("peugeot", "SK", "Trnava Region", "vehicle"): "stellantis",

    # romania
    ("ford", "RO", "Dolj", "vehicle"): "ford otosan",

    # hungary
    ("samsung", "HU", "Pest County", "battery"): "samsung sdi",
    
    # italy
    ("stellantis", "IT", "Torino", "vehicle"): "fiat",
}