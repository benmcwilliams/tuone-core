######
######

# THIS IS JUST A FIRST DRAFT OUTLINE (but it seems to work)

#######
#######

from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient

from functions.utils_recognise_projects import load_articles, yield_full_article_text
from functions.general import read_prompt_from_file_only

# update to load from MongoDB
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

openAI_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(
    api_key=openAI_api_key,
  )

mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["clean_tech_db"]
article_entities_collection = db["article_entities"]

#delete all existing entries in the collection
article_entities_collection.delete_many({})

SKIP_PROJECT_IDS = [
    '1402837'
]

PROMPT_PATH = 'prompts/initial_node_extraction.txt'

def extract_nodes(text, PROMPT_PATH):

    prompt = read_prompt_from_file_only(PROMPT_PATH)

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

    # Ensure JSON is properly loaded
    extracted_nodes = json.loads(completion.choices[0].message.content)

    # Extract the list of nodes correctly
    if "nodes" in extracted_nodes:
        return extracted_nodes["nodes"]
    else:
        raise ValueError("Expected 'nodes' key in LLM output but not found.")

articles_to_process = load_articles()

#this speeds up the search for existing article_ids in mongoDB
article_entities_collection.create_index("article_id", unique=True)

for articleID, text in yield_full_article_text(articles_to_process[:20]):

    if articleID in SKIP_PROJECT_IDS:
        print(f"Skipping Article ID: {articleID} - In skip list.")
        continue

    #check if the article is already in MongoDB
    existing_entry = article_entities_collection.find_one({"article_id": articleID})

    if existing_entry:
        print(f"Skipping Article ID: {articleID} - Already processed.")
        continue  # Skip this article since it's already stored

    print(f"Processing new Article ID: {articleID}")

    nodes = extract_nodes(text, PROMPT_PATH)
    # Store raw extraction + article text in MongoDB
    article_entities_collection.insert_one({
        "article_id": articleID,
        #"article_text": text,  # For now storing full article text for validation purposes.
        "nodes": nodes
    })

print("✅ All articles processed and stored in MongoDB.")