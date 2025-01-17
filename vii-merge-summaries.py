from openai import OpenAI
import os
import json
import re
from src.config.config_paths import PROJECTS_CHRONOLOGICAL, SUMMARIES_EVOLUTIONARY, SUMMARIES_CONTRASTIVE, SUMMARIES_QUALITY, SUMMARIES_COMPRESSIVE, SUMMARIES_MASTER
from src.config.config_paths import PROCESSED_SUMMARIES_MERGED, SUMMARIES_EVOLUTIONARY_CONTRASTIVE
from functions.general import project_needs_update
from functions.utils_summaries import append_sections_within_text_files, read_prompt_with_summaries, write_to_txt_file, additional_notes_on_summary

openAI_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(
    api_key=openAI_api_key,
  )

with open(PROJECTS_CHRONOLOGICAL, 'r') as file:
    projects = json.load(file)

# load (or create) processed_summaries dictionary
if os.path.exists(PROCESSED_SUMMARIES_MERGED):
    with open(PROCESSED_SUMMARIES_MERGED, 'r') as file:
        projects_processed_data = json.load(file)
else:
    projects_processed_data = {}

for projectID, articleIDs in list(projects.items()):

    # paths to existing summaries
    evolutionary_summary_path = f'{SUMMARIES_EVOLUTIONARY}/{projectID}.txt'
    contrastive_summary_path = f'{SUMMARIES_CONTRASTIVE}/{projectID}.txt'

    # define function to read from txt file
    def read_from_txt_file(file_path):
        with open(file_path, 'r') as file:
            return file.read()

    evolutionary_summary = read_from_txt_file(evolutionary_summary_path)
    contrastive_summary = read_from_txt_file(contrastive_summary_path)
    
    #quality_summary_path = f'{SUMMARIES_QUALITY}/{projectID}.txt'
    #compressive_summary_path = f'{SUMMARIES_COMPRESSIVE}/{projectID}.txt'
    #master_summary_path = f'{SUMMARIES_MASTER}/{projectID}.txt'

    #check whether projects needs a new summary generation  
    #needs_update, update_reason = project_needs_update(projectID, articleIDs, projects_processed_data)

    #if not needs_update:
    #    print(f" - Skipping project {projectID} (already processed and up to date).")
    #    continue

    #print(f"## Merging summaries for project {projectID}. Reason: {update_reason}.")

    # append summaries (evolutionary_contrastive is our preferred summary)
    #evolutionary_contrastive_summary = append_sections_within_text_files(evolutionary_summary, contrastive_summary)

    # write the evolutionary_contrastive summary to its own path 

    test_evolutionary_summary = evolutionary_summary + "\n\n" + contrastive_summary
    write_to_txt_file(test_evolutionary_summary, SUMMARIES_EVOLUTIONARY_CONTRASTIVE, f'{projectID}.txt')

    # append quality and compressive summaries
    #quality_compressive_summary = append_sections_within_text_files(quality_summary_path, compressive_summary_path)

    #system_prompt = read_prompt_with_summaries('prompts/summaries/merge_summaries.txt', evolutionary_contrastive_summary)

    #additional_notes = additional_notes_on_summary('gpt-4o-mini', system_prompt, quality_compressive_summary)

    #master_summary = evolutionary_contrastive_summary + "\n\n" + additional_notes

    #write_to_txt_file(master_summary, SUMMARIES_MASTER, f'{projectID}.txt')

    #print(f"Processed {projectID}")

    #update processed projects data with any new projectIDs or article IDs that have just been processed
    #projects_processed_data[projectID] = [int(article_id) for article_id in articleIDs]

    #with open(PROCESSED_SUMMARIES_MERGED, 'w') as file:
    #    json.dump(projects_processed_data, file, indent=4)



