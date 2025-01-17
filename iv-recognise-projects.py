from openai import OpenAI
import json
import os
from functions.utils_recognise_projects import read_all_articles_from_gcs, write_to_jsonl, yield_full_article_text
from functions.general import read_prompt_from_file_only
from src.config.config_paths import GS_ARTICLE_DATABASE

from dotenv import load_dotenv  # Import the load_dotenv function
load_dotenv()  # Load environment variables from .env file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")  # Use the environment variable

openAI_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(
    api_key=openAI_api_key,
  )

SKIP_PROJECT_IDS = [
    '1402837'
]

# File path to articles
prompt_file = 'prompts/project_recognition.txt'

def extract_projects(text):

    prompt = read_prompt_from_file_only(prompt_file)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f''' 
            Here is the article: {text}
            '''
            }
        ],
        temperature=0)

    companies_mentioned = completion.choices[0].message.content
    return companies_mentioned

articles_to_process = read_all_articles_from_gcs(GS_ARTICLE_DATABASE)

for articleID, text in yield_full_article_text(articles_to_process):

    # Skip if article ID is in skip list
    if articleID in SKIP_PROJECT_IDS:
        print(f"Skipping Article ID: {articleID} - In skip list.")
        continue

    output_file_path = f"src/article_project_lists/{articleID}.jsonl"

    # Check if the article's output file already exists
    if os.path.exists(output_file_path):
        print(f"Skipping Article ID: {articleID} - Already processed.")
        continue 

    print(f"Processing Article ID: {articleID}")
    # Extract projects and write the output to a file
    projects = extract_projects(text)
    write_to_jsonl(output_file_path, projects)