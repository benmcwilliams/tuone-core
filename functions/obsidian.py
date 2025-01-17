import pandas as pd
import json
from pathlib import Path
from src.config.config_prompt_tree import get_component_text, tech_dict, phase_dict
from functions.utils import load_mappings

companyID_to_company, locationID_to_location = load_mappings()
tech_id_to_tech = {v: k for k, v in tech_dict.items()}

def get_value_by_id(data, variable, target_id):
    """Retrieve the date for a given ID from the list of dictionaries."""
    for entry in data:
        if entry['ID'] == target_id:
            return entry[variable]
    return None 

def to_json_list(value):
    """
    Convert the 'duplicate_IDs' string into a JSON list.
    
    Rules:
    1) NA or NaN -> []
    2) Comma-separated string -> split on comma
    3) Single string -> wrap in a list
    Returns a JSON string, e.g. '["A","B"]'
    """
    # 1) If it's NaN or 'NA', return an empty list in JSON
    if pd.isna(value) or str(value).strip().upper() == 'NA':
        return json.dumps([])  # "[]"
    
    # 2) If there's a comma, split on comma -> strip spaces
    if ',' in value:
        items = [x.strip() for x in value.split(',') if x.strip()]
        return json.dumps(items)
    
    # 3) Otherwise, wrap the single string in a list
    return json.dumps([value.strip()])

def return_validated_df(directory_path: str) -> tuple[pd.DataFrame, int]:
    """
    Read all Markdown files in a directory and combine their YAML frontmatter into a DataFrame.
    
    Args:
        directory_path (str): Path to directory containing Markdown files
        
    Returns:
        tuple[pd.DataFrame, int]: DataFrame containing metadata from all Markdown files,
                                and count of files found in directory
    """
    # Initialize list to store all metadata
    all_metadata = []
    file_count = 0
    
    # Convert directory path to Path object
    dir_path = Path(directory_path)
    
    # Iterate through all Markdown files in directory
    for md_file in dir_path.glob('*.md'):
        file_count += 1
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract YAML frontmatter (between --- markers)
        if content.startswith('---'):
            # Find the end of the frontmatter
            end_marker = content.find('---', 3)
            if end_marker != -1:
                yaml_content = content[3:end_marker].strip()
                
                # Convert YAML to dictionary
                metadata = {}
                for line in yaml_content.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
                
                # Add filename (without .md) as an additional key in metadata
                metadata['filename'] = md_file.stem  # Add this line
                all_metadata.append(metadata)
    
    # create DataFrame from the collected metadata
    df = pd.DataFrame(all_metadata)

    # check if dataframe is empty
    if df.empty:
        print("Validated dataframe is empty, vault will be initialised with model values")
        return pd.DataFrame(), file_count
    else:
        df.set_index('filename', inplace=True)  # set filename as index
        df.replace({'true': True, 'false': False, "True": True, "False": False}, inplace=True)
        print(df['checked'].unique())
        validated_df = df[df['checked'] == True]
        print("Validated dataframe detected with ", len(validated_df), "projects:")
        print(validated_df[['country', 'location', 'company', 'tech', 'component']].head())
        return validated_df, file_count
    
def return_model_df(directory_path: str) -> pd.DataFrame:
    """
    Read all JSON files in a directory and combine them into a single DataFrame.
    Each JSON file's keys become the index, and the values become columns named after the JSON file.
    
    Args:
        directory_path (str): Path to directory containing JSON files
        
    Returns:
        pd.DataFrame: Combined DataFrame with all JSON data
    """
    # Initialize empty dictionary to store all data
    all_data = {}
    
    # Convert directory path to Path object
    dir_path = Path(directory_path)
    
    # Iterate through all JSON files in directory
    for json_file in dir_path.glob('*.json'):
        # Get the filename without extension to use as column name
        column_name = json_file.stem
        
        # Read JSON file
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        # Add data to dictionary
        all_data[column_name] = data
    
    # Create DataFrame from the collected data
    df = pd.DataFrame.from_dict(all_data, orient='columns')
    
    return df

def clean_model_df(model_df: pd.DataFrame, companyID_to_company: dict, locationID_to_location: dict) -> pd.DataFrame:
    """
    Clean and prepare the model DataFrame by extracting relevant information from the index.
    
    Args:
        model_df (pd.DataFrame): The DataFrame to be cleaned.
        
    Returns:
        pd.DataFrame: The cleaned DataFrame with additional columns.
    """
    model_df['country'] = model_df.index.astype(str).str[:3]
    model_df['location'] = model_df.index.astype(str).str[4:9].map(locationID_to_location)
    model_df['company'] = model_df.index.astype(str).str[10:15].map(companyID_to_company)
    model_df['tech'] = model_df.index.astype(str).str[16:18].map(tech_id_to_tech)
    model_df['component'] = model_df.apply(lambda x: get_component_text(x['tech'], x.name[19:21]), axis=1)
    model_df['phase'] = model_df.index.astype(str).str[22:24].map(phase_dict)

    model_df = model_df[['country','location','company','tech','component','phase','investment_value','capacity','status','dt_announce','dt_actual','dt_operational','dt_cancel', 'jobs']].copy()

    model_df['checked'] = False
    model_df['reject-phase'] = False
    model_df['finetune'] = False
    model_df['share-investment'] = False
    
    return model_df

def get_phases_for_project(projectID):
    # Load phases from capacity.json
    with open('src/outputs/model/phase_level/capacity.json', 'r') as capacity_file:
        phases_data = json.load(capacity_file)

    # Get the first 15 digits of the projectID
    project_prefix = projectID[:15]

    # Find all phase IDs that match the projectID
    matching_phase_ids = [key for key in phases_data.keys() if key.startswith(project_prefix)]

    return matching_phase_ids