import pandas as pd
import json
import os
from src.config.config_prompt_tree import get_component_text, tech_dict, phase_dict
from src.config.config_paths import SUMMARIES_EVOLUTIONARY_CONTRASTIVE
from functions.clean_yaml_files import clean_markdown_yaml
from functions.utils import load_mappings, load_sources_dict, get_source_by_id
from functions.general import save_json_to_file, load_json, load_jsonl 
from functions.obsidian import to_json_list, return_validated_df, return_model_df, clean_model_df, get_value_by_id
from src.config.config_paths import PROJECTS_CHRONOLOGICAL, ARTICLE_ID_DATE_JSONL, ARTICLE_ID_TITLE_JSONL, ARTICLE_ID_URL_JSONL, OBSIDIAN_VAULT_PHASE
from datetime import datetime
from pathlib import Path

# CONFIGURATION
os.makedirs(OBSIDIAN_VAULT_PHASE, exist_ok=True)

#read dictionaries for mapping company, location and tech
companyID_to_company, locationID_to_location = load_mappings()
tech_id_to_tech = {v: k for k, v in tech_dict.items()}

#read in project-articles mapping for appending articles to markdown for each projectID
with open(PROJECTS_CHRONOLOGICAL, 'r') as file:
    project_articles = json.load(file)

article_date_dict = load_jsonl(ARTICLE_ID_DATE_JSONL)
article_title_dict = load_jsonl(ARTICLE_ID_TITLE_JSONL)
source_dict = load_sources_dict('src/source_ID.json')
article_url_dict = load_jsonl(ARTICLE_ID_URL_JSONL)

#ensure all markdown files in vault have type string and not list
vault_path = Path(OBSIDIAN_VAULT_PHASE)
for md_file in vault_path.glob('*.md'):
    clean_markdown_yaml(md_file)

#run the output validated dataframe cleaned function
validated_df, num_files = return_validated_df(OBSIDIAN_VAULT_PHASE)
print(f"Found {num_files} markdown files")

#output timestamped validated dataframe
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
validated_df.to_csv(f"src/outputs/validated/validated_df_{timestamp}.csv")