import json
import os
import pandas as pd
import pickle

def read_jsonl_files_to_dataframe(directory):
    data = []
    invalid_files = []  # List to keep track of files that cannot be parsed

    for file_name in os.listdir(directory):
        if file_name.endswith(".jsonl"):
            file_path = os.path.join(directory, file_name)
            articleID = file_name.replace(".jsonl", "")
            
            try:
                with open(file_path, 'r') as file:
                    for line_number, line in enumerate(file, 1):
                        try:
                            entry = json.loads(line)
                            if isinstance(entry, dict):  # Ensure entry is a dictionary
                                entry['articleID'] = [articleID]
                                data.append(entry)
                            else:
                                print(f"Error in file {file_name}, line {line_number}: Entry is not a dictionary.")
                        except json.JSONDecodeError:
                            print(f"Error in file {file_name}, line {line_number}: Invalid JSON: {line.strip()}")
                            continue  # Skip invalid lines
            except Exception as e:
                print(f"Could not read file {file_path}: {str(e)}")
                invalid_files.append(file_name)  # Add to invalid files list
                continue  # Skip this file if it cannot be read

    # Print the list of invalid files and their count
    if invalid_files:
        print(f"Files that could not be parsed: {invalid_files}")
        print(f"Total number of invalid files: {len(invalid_files)}")

    return pd.DataFrame(data)

def load_name_variations():
    """
    Load company and location name variations from JSON files.

    This function reads the company and location name variations from their respective JSON files,
    creates reverse mappings where each variant is mapped to its main name, and returns these mappings.
    
    Returns:
        tuple: A tuple containing two dictionaries:
            - company_reverse_mapping: A dictionary mapping each variant company name to its main name.
            - location_reverse_mapping: A dictionary mapping each variant location name to its main name.
    """
    # Load company name variations
    with open('src/mappings/company_name_variations.json') as f:
        company_dict = json.load(f)
    company_reverse_mapping = {variant: main_name for main_name, variants in company_dict.items() for variant in variants}

    # Load location name variations
    with open('src/mappings/location_name_variations.json') as f:
        location_dict = json.load(f)
    location_reverse_mapping = {variant: main_name for main_name, variants in location_dict.items() for variant in variants}

    return company_reverse_mapping, location_reverse_mapping

def merge_duplicate_projectIDs(projects_data, project_mapping_file):
    """
    Merges duplicate project IDs in the projects_data dictionary based on mappings 
    provided in the project_mapping_file. It consolidates article IDs associated 
    with duplicate project IDs into a single entry for each primary project ID.
    """
    with open(project_mapping_file, 'r') as f:
        project_mappings = json.load(f)
    
    for key, values in project_mappings.items():
        if key in projects_data:
            for value in values:
                if value in projects_data:
                    projects_data[key].extend(projects_data[value])
                    projects_data[key] = list(set(projects_data[key]))
                    del projects_data[value]
    
    return projects_data

def clean_slashes(df):
    df.columns = [col.replace('\\', '_').replace('/', '_') for col in df.columns]
    df = df.applymap(lambda x: x.replace('\\', '_').replace('/', '_') if isinstance(x, str) else x)
    return df

def flatten_and_unique(series):
    return list(set(item for sublist in series for item in sublist))

def load_company_location_mappings():
    with open('src/mappings/company_to_companyID.pkl', 'rb') as f:
        company_to_companyID = pickle.load(f)

    with open('src/mappings/location_to_locationID.pkl', 'rb') as f:
        location_to_locationID = pickle.load(f)
    
    return company_to_companyID, location_to_locationID

def map_child_to_canonical(master_df, mapping_df):
    """
    Maps instances of (child-location, child-company) to (canonical-location, canonical-company)
    and updates the location_master and company_master columns in the master DataFrame.
    
    Parameters:
        master_df (pd.DataFrame): The master DataFrame containing 'location_master' and 'company_master'.
        mapping_df (pd.DataFrame): The DataFrame containing the mapping between child and canonical locations/companies.
        
    Returns:
        pd.DataFrame: The updated master DataFrame with cleaned 'location_master' and 'company_master'.
    """
    # Merge the master DataFrame with the mapping DataFrame
    merged_df = master_df.merge(
        mapping_df,
        left_on=['location_master', 'company_master'],  # Assuming these are the column names in master_df
        right_on=['child-location', 'child-company'],
        how='left',  # Keep all records from master_df
    )
    
    # Update location_master and company_master with canonical values where available
    merged_df['location_master'] = merged_df['canonical-location'].combine_first(merged_df['location_master'])
    merged_df['company_master'] = merged_df['canonical-company'].combine_first(merged_df['company_master'])
    
    # Drop the original mapping columns
    merged_df = merged_df.drop(columns=['child-location', 'child-company', 'canonical-location', 'canonical-company'])
    
    return merged_df