import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
from src.config.config_paths import PROJECTS_CHRONOLOGICAL, ARTICLE_ID_DATE_JSONL, ARTICLE_ID_TITLE_JSONL, ARTICLE_ID_URL_JSONL, OBSIDIAN_VAULT_PHASE
from src.config.config_paths import SUMMARIES_EVOLUTIONARY_CONTRASTIVE
from src.config.config_prompt_tree import tech_dict
from functions.clean_yaml_files import clean_markdown_yaml
from functions.utils import load_mappings, load_sources_dict, get_source_by_id
from functions.general import load_jsonl 
from functions.return_validated_df import return_validated_df
from functions.obsidian import return_model_df, clean_model_df, get_value_by_id

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

#run the output validated dataframe cleaned function
validated_df, num_files = return_validated_df(OBSIDIAN_VAULT_PHASE)
print(f"Found {num_files} markdown files")

#output timestamped validated dataframe
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
validated_df.to_csv(f"src/outputs/validated/validated_df_{timestamp}.csv")
print("Validated dataframe saved and outputted to src/outputs/validated/validated_df_{timestamp}.csv")

#return latest model_df
model_df = return_model_df('src/outputs/model/phase_level')

#clean model_df (map dictionaries; add NA/False checked | reject | etc columns)
model_df = clean_model_df(model_df, companyID_to_company, locationID_to_location)

# only pass projects that are in project_articles
model_df = model_df[model_df.index.astype(str).str[:15].isin(project_articles.keys())]

#set as output_df and update with validated entries for all cases
output_df = model_df.copy()
output_df.update(validated_df)
output_df.replace("Not disclosed", "-", inplace=True)
print("Output dataframe created and updated with validated entries")

#output timestamped output_df
output_df.to_csv(f"src/outputs/validated/output_df_{timestamp}.csv")
print("Output dataframe saved and outputted to src/outputs/validated/output_df_{timestamp}.csv")

# Set this variable to control whether to update the vault
update_vault = True

#update vault content with output_df
if update_vault:
    print("Updating vault content with output_df")
    for row_index, (phaseID, row) in enumerate(output_df.iterrows()):

        #print which row we are processing out of how many rows there are
        print(f"Processing row {row_index} out of {len(output_df)}")

        #get projectID from phase_id
        projectID = phaseID[:15]

        #load the project summary
        master_summary_path = f'{SUMMARIES_EVOLUTIONARY_CONTRASTIVE}/{projectID}.txt'
        with open(master_summary_path, 'r') as file:
            project_summary = file.read()

        #construct output filename and filepath
        filename = f"{phaseID}.md"
        filepath = os.path.join(OBSIDIAN_VAULT_PHASE, filename)
        
        #construct YAML frontmatter
        yaml_frontmatter = "---\n"
        #every column is mapped directly to the frontmatter with its value for row == projectID
        for column_name in output_df.columns:
            value = row[column_name]
            # Convert value to string in case it's numeric or another data type
            yaml_frontmatter += f"{column_name}: {value}\n"
        yaml_frontmatter += "---\n\n"

        #add summary text
        yaml_frontmatter += f"## {projectID}\n\n"
        yaml_frontmatter += f"{project_summary}\n\n"

        #add article references
        yaml_frontmatter += f"## Article References\n\n"
        articles = project_articles[projectID]
        for article in reversed(articles):
            article = str(article)
            date = get_value_by_id(article_date_dict, "date", article)
            title = get_value_by_id(article_title_dict, "title", article)
            source = get_source_by_id(source_dict, int(article[:2]))
            url = get_value_by_id(article_url_dict, "url", article)
            yaml_frontmatter += f"- {date}, {title}, [{source}]({url})\n"

        #write markdown file to obsidian vault
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(yaml_frontmatter)

