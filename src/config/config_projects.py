import pycountry

COUNTRY_FILTER = [
    'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 
    'HUN', 'ISL', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'NOR', 'POL', 'PRT', 
    'ROU', 'SVK', 'SVN', 'ESP', 'SWE', 'CHE', 'GBR'
]

#COUNTRY_FILTER = [
#    'ITA', 'LTU', 'LVA', 'EST', 'FIN', 'ESP', 'PRT', 'AUT', 'BEL', 'BRG', 'NLD'
#]

## Defining variables and paths 
DROP_LOCATIONS = ['NA', 'Not specified', '', 'Unknown', 'N/A', 'Europe', 'UK', "Great Britain", 'North America', 'Global', 'U.S.', 'TBD', 'Central Europe', 'Undisclosed',
                  'Eastern Germany','eastern Germany', 'North of England', 'Northern England', 'northern England', "Scotland", "Wales", "Italy", "Electrolyser Production",
                  "Italian plant", "Refinery", "Southern Italy", "Northern and Central Italy", "Southern Estonia", "southern Spain", "Southern Spain",
                  "Northern and Central Italy"]

COUNTRIES = [country.name for country in pycountry.countries] + \
            [country.alpha_2 for country in pycountry.countries] + \
            [country.alpha_3 for country in pycountry.countries] + \
            [country.official_name for country in pycountry.countries if hasattr(country, 'official_name')]

DROP_COMPANIES = ["Unknown", "Unnamed Spanish power trader", "Ignore", "European Solar Manufacturing Council", "European Clean Hydrogen Alliance",
                  "European Heat Pump Association", "Hydrogen Europe", "Joint Research Centre"]


