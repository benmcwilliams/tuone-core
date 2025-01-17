from openai import OpenAI
import os
import json
import tiktoken
from functions.utils import load_mappings
from src.config.config_paths import PROMPT_SUMMARY_ORIGINAL, PROJECTS_CHRONOLOGICAL, GS_ARTICLE_DATABASE, PROCESSED_SUMMARIES_ROOT
from src.config.config_paths import PROMPT_SUMMARY_EVOLUTIONARY, PROMPT_SUMMARY_COMPRESSIVE, PROMPT_SUMMARY_QUALITY, PROMPT_SUMMARY_CONTRASTIVE
from functions.utils_recognise_projects import read_all_articles_from_gcs
from functions.utils import build_article_lookup_dict
from functions.utils_summaries import get_full_articles_from_IDs, generate_summary, write_to_txt_file
from functions.general import read_prompt_from_file_only, project_needs_update

openAI_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(
    api_key=openAI_api_key,
  )

tokenizer = tiktoken.get_encoding("cl100k_base")

# define summary prompt path dictionary
summary_prompt_path_dict = {
    'original': PROMPT_SUMMARY_ORIGINAL,
    'evolutionary': PROMPT_SUMMARY_EVOLUTIONARY,
    'compressive': PROMPT_SUMMARY_COMPRESSIVE,
    'quality': PROMPT_SUMMARY_QUALITY,
    'contrastive': PROMPT_SUMMARY_CONTRASTIVE
}

# load mappings
companyID_to_company, locationID_to_location = load_mappings()

# load articles and projects
articles = read_all_articles_from_gcs(GS_ARTICLE_DATABASE)

with open(PROJECTS_CHRONOLOGICAL, 'r') as file:
    projects = json.load(file)

#build article lookup dictionary
article_lookup = build_article_lookup_dict(articles)

#define summary type
for summary_type in ['evolutionary', 'contrastive']:

    # load (or create) processed_summaries dictionary
    PROCESSED_SUMMARIES_PATH = PROCESSED_SUMMARIES_ROOT + "-" + summary_type + ".json"
    print(PROCESSED_SUMMARIES_PATH)

    if os.path.exists(PROCESSED_SUMMARIES_PATH):
        with open(PROCESSED_SUMMARIES_PATH, 'r') as file:
            projects_processed_data = json.load(file)
    else:
        projects_processed_data = {}

    print(f"## Processing summary type: {summary_type}")
    summary_prompt = read_prompt_from_file_only(summary_prompt_path_dict[summary_type])
    output_summary_folder_path = f'src/outputs/summaries/{summary_type}'

    # loop through projects and generate summaries
    for projectID, articleIDs in list(projects.items()):

        country = projectID[:3]
        locationID = projectID[4:9]
        companyID = projectID[10:15]
        location = locationID_to_location.get(locationID, 'Unknown Location')
        company = companyID_to_company.get(companyID, 'Unknown Company')
        
        #check whether projects needs a new summary generation  
        needs_update, update_reason = project_needs_update(projectID, articleIDs, projects_processed_data)

        if not needs_update:
            print(f" - Skipping project {projectID} (already processed and up to date).")
            continue

        print(f"## Processing project: {company}, {location}, {country}. Reason: {update_reason}. ID: {projectID}")

        #return articles that discuss the project
        article_texts = get_full_articles_from_IDs(article_lookup, articleIDs)

        # Ensure article_texts is a single string by extracting 'main_text' and count tokens
        token_count_article_texts = " ".join(article['main_text'] for article in article_texts)
        num_tokens = len(tokenizer.encode(token_count_article_texts))
        print(f"Number of tokens in article_texts: {num_tokens}")

        if num_tokens > 100000:  # Lowered threshold to account for prompt tokens
            # Limit the number of articles to fit within the token limit
            max_tokens = 100000
            limited_articles = []
            total_tokens = 0
            
            for article in article_texts:
                article_tokens = len(tokenizer.encode(article['main_text']))
                if total_tokens + article_tokens > max_tokens:
                    break
                limited_articles.append(article)
                total_tokens += article_tokens
            
            print(f"Reduced from {len(article_texts)} to {len(limited_articles)} articles to stay within token limit.")
            article_texts = limited_articles

        #summarise relevant information about the project from those articles
        summary = generate_summary('gpt-4o-mini', summary_prompt, company, location, country, article_texts)

        #save summary to file
        output_filename = f"{projectID}.txt"
        output_file_path = os.path.join(output_summary_folder_path, output_filename)
        write_to_txt_file(summary, output_summary_folder_path, output_filename)

        #uppdate processed projects data with any new projectIDs or article IDs that have just been processed
        projects_processed_data[projectID] = [int(article_id) for article_id in articleIDs]

        with open(PROCESSED_SUMMARIES_PATH, 'w') as file:
            json.dump(projects_processed_data, file, indent=4)
