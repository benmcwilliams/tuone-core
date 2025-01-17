import json
import os
from functions.filter_utils import gen_ID_dictionary, upload_to_gcs
from functions.keyword_filter import process_articles, load_dictionary, filter_articles
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "src/config/tuone-446608-44616a115888.json"
from google.cloud import storage  # Import the Google Cloud Storage library

jsonl_directory_path = 'src/database_articles'
dates_output_file_path = 'src/outputs/article_dictionaries/article_ID_date.jsonl'
urls_output_file_path = 'src/outputs/article_dictionaries/article_ID_URL.jsonl'
titles_output_file_path = 'src/outputs/article_dictionaries/article_ID_title.jsonl'
keyword_output_file_path = 'src/outputs/article_dictionaries/article_ID_keywords.jsonl'
article_database_output_path = "src/article_database.jsonl"

# Define keywords to filter for
keywords = {"factory", "facility", "plant", "production line", "production site", "refinery", "pilot project"}

# Clear the keyword output file before processing
open(keyword_output_file_path, 'w').close()  # This will empty the file

# Get all JSONL files in the specified directory
jsonl_file_paths = [os.path.join(jsonl_directory_path, f) for f in os.listdir(jsonl_directory_path) if f.endswith('.jsonl')]

# Call the generic function for each type of dictionary
gen_ID_dictionary(jsonl_file_paths, dates_output_file_path, 'date')
gen_ID_dictionary(jsonl_file_paths, urls_output_file_path, 'url')
gen_ID_dictionary(jsonl_file_paths, titles_output_file_path, 'title')

# Process articles for keyword filtering
for jsonl_file_path in jsonl_file_paths:
    process_articles(jsonl_file_path, keyword_output_file_path, keywords)  # Pass keywords as an argument

print(f"Data has been written to {dates_output_file_path}")
print(f"Data has been written to {urls_output_file_path}")
print(f"Data has been written to {titles_output_file_path}")
print(f"Keyword processing results saved to {keyword_output_file_path}")

# Load the IDs with 'Y' from the dictionary
ids_with_keywords = load_dictionary(keyword_output_file_path)

# Filter the articles based on those IDs and output to the new file
filter_articles(jsonl_file_paths, article_database_output_path, ids_with_keywords)

# Upload the output file to Google Cloud Storage
upload_to_gcs('tuone-article-database', article_database_output_path, 'article_database.jsonl')  # Specify your desired path in the bucket