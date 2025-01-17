import json
import os
import pandas as pd
import numpy as np
import re
import ast

def read_prompt_from_file_only(file_path):
    """
    Reads the prompt from an external file.
    """
    with open(file_path, 'r') as file:
        prompt = file.read()
    return prompt

def read_prompt_from_file(file_path, **kwargs):
    """
    Reads the prompt from an external file and formats it with the given parameters.
    Accepts any number of keyword arguments for formatting.
    """
    with open(file_path, 'r') as file:
        prompt_template = file.read()

    # Substitute placeholders with actual values
    prompt = prompt_template.format(**kwargs)
    
    return prompt

def read_text_file(file_path):
    """Reads a text file and returns its content as a string."""
    with open(file_path, 'r') as file:
        return file.read()

def save_jsonl(file_path, json_string):
    # Open the file in append mode ('a') to add the json_string as a new line
    with open(file_path, 'w') as file:
        # Write the json_string to the file as a single line
        file.write(json_string + '\n')

def save_json_to_file(data, file_path):
    """Saves the given data to a JSON file at the specified file path."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def load_json(file_path):
    """Load JSON data from a file and return it. If the file does not exist, return an empty dictionary."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    
def load_jsonl(file_path):
    """Load JSONL data from a file and return it as a list of dictionaries. If the file does not exist, return an empty list."""
    try:
        with open(file_path, 'r') as file:
            return [json.loads(line) for line in file]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def project_needs_update(projectID, new_article_ids, projects_processed_data):
    """
    Check if a project has already been processed and if its article list has changed.
    Returns True if the project needs an update and whether it's a new project or has new articles.
    """
    if projectID not in projects_processed_data:
        # New project
        return True, "new_project"
    
    # Existing project: Check if the article list has changed
    existing_article_ids = projects_processed_data[projectID]
    if sorted(existing_article_ids) != sorted(new_article_ids):
        return True, "new_articles"
    
    # No updates needed
    return False, None

def write_to_file(output_path, content):
    with open(output_path, "w") as file:
        file.write(content)

def get_prompts(company, location, country, paths, value=None):
    """Fetch all required prompts for the project."""
    return {
        'describe_investment': read_prompt_from_file(paths['describe_investment'], company, location, country),

        'return_tech': read_prompt_from_file(paths['return_tech'], company, location, country),
        'component_battery': read_prompt_from_file(paths['component_battery'], company, location, country),
        'component_vehicle': read_prompt_from_file(paths['component_vehicle'], company, location, country),
        'component_solar': read_prompt_from_file(paths['component_solar'], company, location, country),
        'component_hydrogen': read_prompt_from_file(paths['component_hydrogen'], company, location, country),
        'component_wind': read_prompt_from_file(paths['component_wind'], company, location, country),

        'expansion_count': read_prompt_from_file(paths['expansion_count'], company, location, country),
        'expansion_describe': read_prompt_from_file(paths['expansion_describe'], company, location, country),
        'expansion_investments': read_prompt_from_file(paths['expansion_investments'], company, location, country, value),
        'expansion_capacities': read_prompt_from_file(paths['expansion_capacities'], company, location, country, value),
        'expansion_statuses': read_prompt_from_file(paths['expansion_statuses'], company, location, country, value),
        'expansion_dates_announce': read_prompt_from_file(paths['expansion_dates_announce'], company, location, country, value),
        'expansion_dates_construct': read_prompt_from_file(paths['expansion_dates_construct'], company, location, country, value),
        'expansion_dates_operate': read_prompt_from_file(paths['expansion_dates_operate'], company, location, country, value),

        'return_investment': read_prompt_from_file(paths['return_investment'], company, location, country),
        'return_capacity': read_prompt_from_file(paths['return_capacity'], company, location, country),
        'return_status': read_prompt_from_file(paths['return_status'], company, location, country),
        'return_date_announce': read_prompt_from_file(paths['return_date_announce'], company, location, country),
        'return_date_construct': read_prompt_from_file(paths['return_date_construct'], company, location, country),
        'return_date_operate': read_prompt_from_file(paths['return_date_operate'], company, location, country),
        # Add other prompts as needed...
    }

def project_needs_update(projectID, new_article_ids, projects_data):
    """
    Check if a project has already been processed and if its article list has changed.
    Returns True if the project needs an update and whether it's a new project or has new articles.
    """
    if projectID not in projects_data:
        # New project
        return True, "new_project"
    
    # Existing project: Check if the article list has changed
    existing_article_ids = projects_data[projectID]
    if sorted(existing_article_ids) != sorted(new_article_ids):
        return True, "new_articles"
    
    # No updates needed
    return False, None

# Load the project_id_list from "filtered_projects.json"
def load_project_ids_from_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return list(data.keys())

# Function to merge multiple JSON files into a pandas DataFrame, filtering by project_id_list
def merge_json_files(json_files, project_id_list):
    # Initialize an empty DataFrame
    df = pd.DataFrame()

    # Loop over each JSON file and add data as a new column
    for file in json_files:
        # Load the JSON data
        data = load_json(file)

        # Create a DataFrame from the current JSON dictionary, filtering by project_id_list
        temp_df = pd.DataFrame(
            [(k, v) for k, v in data.items() if k in project_id_list],
            columns=['projectID', os.path.basename(file).replace('.json', '')]
        )

        # Merge with the main DataFrame on 'projectID'
        if df.empty:
            df = temp_df  # If df is empty, just assign it
        else:
            df = pd.merge(df, temp_df, on='projectID', how='outer')  # Merge on 'projectID'

    return df

def convert_string_to_list(value):
    """
    Converts string representations of lists into actual lists. 
    If the value is not a string list, returns the value as-is.
    """
    if isinstance(value, str):
        try:
            if value.startswith('[') and value.endswith(']'):
                return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            pass
    return value

def clean_list_formatting(value):
    """
    Function to remove the Python code formatting and return the list as a string.
    """
    if isinstance(value, str):
        cleaned_value = re.sub(r"```python\n|\n```", "", value)
        return cleaned_value.strip()
    return value

def clean_value(value):
    """
    Cleans a single value for YAML compatibility:
    - Converts string representations of lists into proper lists
    - Converts NaN values to None
    - Converts booleans to their native format
    - Converts everything else to string if necessary
    """
    value = convert_string_to_list(value)
    if isinstance(value, list):
        return [clean_value(v) for v in value]
    elif pd.isna(value) or value == 'nan':
        return None
    elif isinstance(value, bool):
        return value
    elif isinstance(value, (int, float)) and not np.isnan(value):
        return value
    else:
        return str(value)
    
def clean_dataframe(df):
    """
    Cleans all values in the dataframe to be YAML-compatible by applying
    the clean_value function to each element.
    """
    return df.applymap(clean_value)

def convert_double_to_single_quotes(value):
    """
    Function to convert a list with double-quoted strings to single-quoted strings.
    """
    if isinstance(value, str):
        try:
            parsed_value = ast.literal_eval(value)
            if isinstance(parsed_value, list):
                return str(parsed_value).replace('"', "'")
        except (ValueError, SyntaxError):
            pass
    return value