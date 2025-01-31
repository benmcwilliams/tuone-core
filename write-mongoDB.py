import os
from frontmatter import Frontmatter
import pymongo
from src.config.config_paths import OBSIDIAN_VAULT_PHASE
from src.config.mongoDB import INVESTMENT_PHASE_FIELDS
import subprocess  # Add this import at the top

def get_git_branch():
    """Get the current git branch name."""
    try:
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("Warning: Could not get git branch name. Using 'main' as default.")
        return 'main'

#establish MongoDB Connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
#db_name = f"{get_git_branch()}"  # Use git branch in database name
db_name = "ben_latest"
db = client[db_name]
collection = db["projects"]
#collection.delete_many({})
#print("All documents from {} deleted".format(collection.name))

def normalize_yaml_data(metadata):
    """Ensures that YAML metadata follows a consistent structure."""
    #print("BEFORE normalization:", {k: metadata.get(k) for k in ['checked', 'finetune']})
    
    cleaned_data = {}

    for key, expected_type in INVESTMENT_PHASE_FIELDS.items():
        value = metadata.get(key, None)  # Get field value or default to None
        
        # If the field is missing or just a dash, assign a sensible default
        if value is None or value == "-":
            cleaned_data[key] = "" if expected_type is str else False
            continue
        
        # Ensure boolean fields are correctly parsed
        if expected_type is bool:
            # Handle various forms of boolean values
            if isinstance(value, str):
                value = value.lower().strip()
                cleaned_data[key] = value in ['true', '1', 'yes', 'on']
            else:
                cleaned_data[key] = bool(value)
        
        # Handle string fields
        elif expected_type is str:
            if isinstance(value, list):
                # Convert list to comma-separated string
                cleaned_data[key] = ", ".join(str(item) for item in value if item and item != "-")
            else:
                # Convert to string, handle dash case
                str_value = str(value)
                cleaned_data[key] = "" if str_value == "-" else str_value
    
    #print("AFTER normalization:", {k: cleaned_data.get(k) for k in ['checked', 'finetune']})
    return cleaned_data

def process_markdown_files(directory, debug=False):
    """Reads markdown files, extracts YAML data, and stores in MongoDB."""
    if debug:
        # Debug: Process only one file
        test_file = "GBR-06634-00032_01_05_00.md"  # Replace with your specific test file name
        files_to_process = [test_file]
        print(f"DEBUG MODE: Processing only {test_file}")
    else:
        files_to_process = [f for f in os.listdir(directory) if f.endswith(".md")]
        
    for filename in files_to_process:
        file_path = os.path.join(directory, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Replace single dashes with empty strings in the YAML section
                lines = content.split('\n')
                in_frontmatter = False
                processed_lines = []
                
                for line in lines:
                    if line.strip() == '---':
                        in_frontmatter = not in_frontmatter
                        processed_lines.append(line)
                        continue
                        
                    if in_frontmatter and ': -' in line:
                        # Replace ': -' with ': ""' in frontmatter
                        line = line.replace(': -', ': ""')
                    
                    processed_lines.append(line)
                
                processed_content = '\n'.join(processed_lines)
                post = Frontmatter.read(processed_content)
                
                # Add these debug prints
                print(f"\nRaw YAML for {filename}:", post['attributes'])
                print("Field types:")
                for key, value in post['attributes'].items():
                    print(f"{key}: {type(value)}")
            
            # Clean and normalize metadata
            cleaned_metadata = normalize_yaml_data(post['attributes'])
            
            # Store document with filename as ID
            document = {
                "_id": filename,
                **cleaned_metadata  # Spread the metadata directly into the document
            }
            
            # Insert or update the document in MongoDB
            collection.update_one(
                {"_id": document["_id"]}, 
                {"$set": document}, 
                upsert=True
            )
            
            print(f"Stored: {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")

#run the script
process_markdown_files(OBSIDIAN_VAULT_PHASE, debug=False)  # Set to False for processing all files