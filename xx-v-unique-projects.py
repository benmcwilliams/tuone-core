import json
import pandas as pd
import pickle

from src.config.config_projects import COUNTRY_FILTER, DROP_LOCATIONS, COUNTRIES, DROP_COMPANIES
from src.config.config_paths import PROJECT_ARTICLE_LISTS, DUPLICATE_PROJECTS_PATH, RECOGNISED_PROJECTS_JSON, RECOGNISED_PROJECTS_CSV
from src.config.config_paths import METADATA_PATH, DUPLICATES_PATH, NEW_DUPLICATES_PATH, ARTICLE_ID_DATE_JSONL, PROJECTS_CHRONOLOGICAL

from functions.projects_utils import read_jsonl_files_to_dataframe, map_child_to_canonical
from functions.projects_utils import load_company_location_mappings, load_name_variations, clean_slashes, flatten_and_unique
from functions.sort_project_collections import return_sorted_project_collection

#read tuples dictionary
tuples_df = pd.read_excel('src/inputs/canonical_nodes.xlsx')

#read company and location name variations and dictionaries
company_reverse_mapping, location_reverse_mapping = load_name_variations()
company_to_companyID, location_to_locationID = load_company_location_mappings()

#read article-project lists to a dataframe; filter out obviously wrong locations 
df = read_jsonl_files_to_dataframe(PROJECT_ARTICLE_LISTS)
df_cleaned = df[~df['location'].isin(DROP_LOCATIONS + COUNTRIES)].copy()

#replace company and location names with masters
df_cleaned['company_master'] = df_cleaned['company'].replace(company_reverse_mapping)
df_cleaned['location_master'] = df_cleaned['location'].replace(location_reverse_mapping)

#filter out obviously wrong companies (like "Unknown" or "Unnamed Spanish power trader" but also "Ignore" that is mapped)
df_cleaned = df_cleaned[~df_cleaned['company_master'].isin(DROP_COMPANIES)].copy()

#filter for country selector
df_cleaned = df_cleaned[df_cleaned['country'].isin(COUNTRY_FILTER)].copy() 
df_cleaned = clean_slashes(df_cleaned)
print(len(df_cleaned['company'].unique()), "company names identified and reduced to", len(df_cleaned['company_master'].unique()), "unique names")
print(len(df_cleaned['location'].unique()), "location names identified and reduced to", len(df_cleaned['location_master'].unique()), "unique names")

#apply tuples dictionary to company and location
df_cleaned = map_child_to_canonical(df_cleaned, tuples_df)
print("--- After tuple reduction, there are", len(df_cleaned['company_master'].unique()), "unique company names")
print("--- After tuple reduction, there are", len(df_cleaned['location_master'].unique()), "unique location names")

#groupby company, location, country and aggregate articles and tech
all_projects = df_cleaned.groupby(['company_master', 'location_master', 'country']).agg({
    'articleID': flatten_and_unique,  # Flatten and remove duplicates
    'tech': lambda x: list(x.unique())  # Keep unique tech values
}).reset_index()

all_projects['companyID'] = all_projects['company_master'].map(company_to_companyID)
all_projects['locationID'] = all_projects['location_master'].map(location_to_locationID)
print("Project recognition phase recognises {} projects".format(len(all_projects)))

### assign IDs to any new projects

#set start of new IDs dictionary from max_previous+1
new_companyID_start = max(int(id_val) for id_val in company_to_companyID.values()) + 1
new_locationID_start = max(int(id_val) for id_val in location_to_locationID.values()) + 1

#identify unique companies and locations where companyID and locationID are NA (these are new company and locations which need an ID assigned)
unique_na_companies = all_projects[all_projects['companyID'].isna()]['company_master'].unique()
unique_na_locations = all_projects[all_projects['locationID'].isna()]['location_master'].unique()

#create dictionaries for new company and location IDs
new_companyIDs = {company: str(new_companyID_start + i).zfill(5) for i, company in enumerate(unique_na_companies)}
new_locationIDs = {location: str(new_locationID_start + i).zfill(5) for i, location in enumerate(unique_na_locations)}

#apply the new IDs to the dataframe
all_projects['companyID'] = all_projects['company_master'].map(new_companyIDs).fillna(all_projects['companyID'])
all_projects['locationID'] = all_projects['location_master'].map(new_locationIDs).fillna(all_projects['locationID'])

#create projectID
all_projects['projectID'] = all_projects['country'] + '-' + all_projects['locationID'] + '-' + all_projects['companyID']

#save results to csv
all_projects[['projectID', 'country', 'location_master', 'company_master', 'articleID']].to_csv(RECOGNISED_PROJECTS_CSV, index=False)
print("Writing all_projects.csv with {} projects".format(len(all_projects)))

### output projectID : articleIDs JSON dictionary

all_projects_filter = all_projects[['projectID', 'articleID']].copy()

projects_data = {row['projectID']: [int(article_id) for article_id in row['articleID']] for _, row in all_projects_filter.iterrows()}
all_projects_len = len(projects_data)
print(f"--- writing {len(projects_data)} projects to JSON")

with open(RECOGNISED_PROJECTS_JSON, 'w') as file:
    json.dump(projects_data, file, indent=4)
print(f"Data written to {RECOGNISED_PROJECTS_JSON}")

# sort projects by date
sorted_project_data = return_sorted_project_collection(RECOGNISED_PROJECTS_JSON, ARTICLE_ID_DATE_JSONL)

# Write out the sorted result
with open(PROJECTS_CHRONOLOGICAL, 'w', encoding='utf-8') as f:
    json.dump(sorted_project_data, f, indent=4, ensure_ascii=False)
print(f"Data written to {PROJECTS_CHRONOLOGICAL}")

# update company and location dictionaries with new IDs
company_to_companyID.update(new_companyIDs)
location_to_locationID.update(new_locationIDs)

# save dictionaries as pickles
with open('src/mappings/company_to_companyID.pkl', 'wb') as f:
    pickle.dump(company_to_companyID, f)

with open('src/mappings/location_to_locationID.pkl', 'wb') as f:
    pickle.dump(location_to_locationID, f)

print("Fresh dictionaries saved as pickles successfully!")