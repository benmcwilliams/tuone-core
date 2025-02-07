from openai import OpenAI
import os
import json
from pymongo import MongoClient
from src.config.config_paths import GS_ARTICLE_DATABASE, PROMPT_EXTRACT_NODES
from functions.utils_recognise_projects import read_all_articles_from_gcs

#initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

#initialize MongoDB connection (Optional)
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["knowledge_graph"]
#delete the existing nodes collection
db.drop_collection("nodes")
nodes_collection = db["nodes"]

#connect to Google Cloud Storage
print("🔗 Connecting to Google Cloud Storage ....")
articles = read_all_articles_from_gcs(GS_ARTICLE_DATABASE)

#load node extraction prompt 
with open(PROMPT_EXTRACT_NODES, "r") as f:
    node_extraction_prompt = f.read()

#function to call an LLM model for extracting nodes
def extract_nodes(article_text, model="gpt-4o-mini"):
    """
    Calls GPT-4 to extract structured nodes from an article.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": node_extraction_prompt},
            {"role": "user", "content": article_text}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )

    try:
        nodes_data = json.loads(response.choices[0].message.content)
        return nodes_data.get("nodes", [])
    except Exception as e:
        print(f"⚠️ Error parsing LLM response: {e}")
        return []

def flatten_article_text(article):
    """
    Flattens an article's title and paragraphs into a single string,
    filtering out boilerplate content.
    
    Args:
        article (dict): Article dictionary containing 'title' and 'paragraphs'
    
    Returns:
        str: Flattened article text
    """
    # Start with the title
    text_parts = [article['title']]
    
    for p_text in article['paragraphs'].values():
        # Skip paragraphs containing boilerplate content
        text_parts.append(p_text)
    
    # Join with newlines
    return '\n\n'.join(text_parts)

def write_nodes_to_mongodb(nodes, article_id):
    """
    Writes extracted nodes to MongoDB.
    
    Args:
        nodes (list): List of nodes to be written to the database.
        article_id (str): ID of the article from which nodes were extracted.
    """
    if not nodes:
        print(f"⚠️ No nodes to write for article {article_id}")
        return

    try:
        # Prepare nodes with article ID
        nodes_with_id = [{"article_id": article_id, **node} for node in nodes]
        nodes_collection.insert_many(nodes_with_id)
        print(f"✅ Successfully wrote nodes for article {article_id} to MongoDB")
    except Exception as e:
        print(f"⚠️ Error writing nodes to MongoDB for article {article_id}: {e}")


# Update the article processing loop
for article in articles[:3]:  # Process first 2 articles for testing
    print(f"📄 Processing article: {article['meta']['ID']}")
    article_text = flatten_article_text(article)
    extracted_nodes = extract_nodes(article_text)
    write_nodes_to_mongodb(extracted_nodes, article['meta']['ID'])