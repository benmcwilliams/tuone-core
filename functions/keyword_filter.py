# keyword_filter.py
import json
import re

def merge_article_content(article_data):
    """
    Merge the title and all paragraphs into a single string.
    """
    title = article_data.get("title", "")
    paragraphs = article_data.get("paragraphs", {}).values()
    merged_content = f"{title} " + " ".join(paragraphs)
    return merged_content

def keyword_in_text(text, keywords):
    """
    Check if any of the keywords are present in the text.
    """
    text_lower = text.lower()
    for keyword in keywords:
        # Use regex to ensure we match whole words (and not partial words)
        if re.search(rf"\b{re.escape(keyword)}\b", text_lower):
            return True
    return False

def process_articles(input_file_path, output_file_path, keywords):
    """
    Read articles from JSONL, check for keywords, and write the result to JSONL.
    """
    try:
        with open(input_file_path, 'r') as infile, open(output_file_path, 'a') as outfile:
            for line in infile:
                article_data = json.loads(line)
                article_id = article_data.get("meta", {}).get("ID", "Unknown ID")
                merged_content = merge_article_content(article_data)
                
                # Check if any keyword is found in the merged content
                has_keyword = keyword_in_text(merged_content, keywords)
                result = {"ID": article_id, "keywords_present": "Y" if has_keyword else "N"}
                
                # Write the result to the output JSONL file
                json.dump(result, outfile)
                outfile.write("\n")

        print(f"Processing complete. Results saved to {output_file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

### Write the new database out. 

def load_dictionary(dictionary_file_path):
    """
    Load the dictionary containing the IDs and the keyword presence (Y/N).
    Returns a set of IDs where the keyword presence is 'Y'.
    """
    ids_with_keywords = set()
    try:
        with open(dictionary_file_path, 'r') as dictionary_file:
            for line in dictionary_file:
                entry = json.loads(line)
                if entry.get("keywords_present") == "Y":
                    ids_with_keywords.add(entry.get("ID"))
    except Exception as e:
        print(f"Error loading dictionary: {e}")
    return ids_with_keywords

def filter_articles(input_file_paths, output_file_path, ids_with_keywords):
    """
    Filter the articles from the input JSONL files based on the IDs that have 'Y' in the dictionary.
    """
    try:
        with open(output_file_path, 'w') as outfile:  # Open output file once
            for input_file_path in input_file_paths:  # Updated to handle a list of files
                with open(input_file_path, 'r') as infile:
                    for line in infile:
                        article_data = json.loads(line)
                        article_id = article_data.get("meta", {}).get("ID", "")
                        
                        if article_id in ids_with_keywords:
                            json.dump(article_data, outfile)
                            outfile.write("\n")
        
        print(f"Filtered articles have been saved to {output_file_path}")
    except Exception as e:
        print(f"An error occurred during filtering: {e}")