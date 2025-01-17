# article_utils.py
import json
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "src/config/tuone-446608-44616a115888.json"
from google.cloud import storage  # Import the Google Cloud Storage library

def gen_ID_dictionary(jsonl_file_paths, output_file_path, field_name):
    article_info = []

    for jsonl_file_path in jsonl_file_paths:
        with open(jsonl_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                entry = json.loads(line.strip())
                article_id = entry['meta']['ID']
                
                # Check if the field_name is 'title' or another field
                if field_name == 'title':
                    field_value = entry.get('title')  # Get title directly from entry
                else:
                    field_value = entry['meta'].get(field_name)  # Get from meta for other fields

                # Check if the field value is None
                if field_value is None:
                    print(f"Warning: Missing or None value for '{field_name}' for article ID: {article_id}")
                    continue  # Skip this entry or handle it as needed

                # Append to the list as a dictionary
                article_info.append({'ID': article_id, field_name: field_value})

    # Write the output to a new JSONL file
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        for article in article_info:
            # Convert dictionary to JSON string and write to the file
            json_line = json.dumps(article)
            output_file.write(json_line + '\n')

# Function to upload a file to Google Cloud Storage
def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")