from pathlib import Path
import pandas as pd
import yaml
import re

def return_validated_df(directory_path: str) -> tuple[pd.DataFrame, int]:
    """
    Read all Markdown files in a directory, clean their YAML frontmatter, 
    and combine the metadata into a DataFrame.

    Args:
        directory_path (str): Path to directory containing Markdown files
        
    Returns:
        tuple[pd.DataFrame, int]: DataFrame containing metadata from all Markdown files,
                                  and count of files found in directory
    """
    def clean_yaml(yaml_content: str) -> dict:
        """
        Cleans and normalizes a YAML frontmatter string.

        Args:
            yaml_content (str): Raw YAML frontmatter as a string
        
        Returns:
            dict: Cleaned YAML as a dictionary
        """
        # Normalize problematic values
        yaml_content = re.sub(r':\s*-$', ': null', yaml_content, flags=re.MULTILINE)
        yaml_content = re.sub(r':\s*NA$', ': null', yaml_content, flags=re.MULTILINE)
        
        # Parse YAML safely
        try:
            yaml_data = yaml.safe_load(yaml_content)
            if yaml_data is None:
                yaml_data = {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            yaml_data = {}
        
        return yaml_data

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
                
                # Clean and normalize the YAML frontmatter
                metadata = clean_yaml(yaml_content)
                
                # Add filename (without .md) as an additional key in metadata
                metadata['filename'] = md_file.stem
                all_metadata.append(metadata)
    
    # Create DataFrame from the collected metadata
    df = pd.DataFrame(all_metadata)

    # Check if dataframe is empty
    if df.empty:
        print("Validated dataframe is empty, vault will be initialised with model values")
        return pd.DataFrame(), file_count
    else:
        df.set_index('filename', inplace=True)  # Set filename as index
        df.replace({'true': True, 'false': False, "True": True, "False": False}, inplace=True)
        print(df['checked'].unique())
        validated_df = df[df['checked'] == True]
        print("Validated dataframe detected with ", len(validated_df), "projects:")
        print(validated_df[['country', 'location', 'company', 'tech', 'component']].head())
        return validated_df, file_count