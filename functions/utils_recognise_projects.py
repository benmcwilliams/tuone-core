import json
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "src/config/tuone-446608-44616a115888.json"
from google.cloud import storage  # Import the Google Cloud Storage library

def read_all_articles_from_gcs(file_path):
    """
    Read all articles from a JSONL file in Google Cloud Storage.

    Parameters:
    file_path (str): Path to the input JSONL file with all articles.

    Returns:
    List[dict]: A list of all articles read from the JSONL file.
    """
    # Extract bucket name and file name from the GCS path
    gcs_path_parts = file_path.split('/', 3)
    bucket_name = gcs_path_parts[2]
    file_name = gcs_path_parts[3]

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    content = blob.download_as_text()
    
    # Parse the JSONL content
    articles = [json.loads(line) for line in content.splitlines()]
    
    return articles

def yield_full_article_text(articles):
    """
    Process a list of articles and extract the article ID and combined text for each.

    Parameters:
    articles (list): List of articles to process.

    Yields:
    Tuple: article ID and combined text string for each article.
    """
    for article in articles:
        # Extract the article ID from the "meta" section
        article_id = article.get("meta", {}).get("ID", "Unknown ID")
        
        # Extract title and paragraphs
        title = article.get("title", "")
        paragraphs = article.get("paragraphs", {})
        combined_paragraphs = " ".join(paragraphs.values())
        
        # Combine the title and paragraphs
        full_text = f"{title} {combined_paragraphs}"
        
        # Yield the article ID and combined text
        yield article_id, full_text

def write_to_jsonl(file_path, response_text):
    # Remove the format indicator if necessary
    if response_text.startswith('```jsonl'):
        response_text = response_text[len('```jsonl\n'):-len('\n```')]
    elif response_text.startswith('```json'):
        response_text = response_text[len('```json\n'):-len('\n```')]

    # Split the cleaned response into lines
    jsonl_lines = response_text.strip().split('\n')
    
    # Open the file in append mode and write each cleaned JSON line
    with open(file_path, 'w') as file:
        for jsonl_line in jsonl_lines:
            if jsonl_line:  # Ensure it's not an empty line
                file.write(jsonl_line + '\n')