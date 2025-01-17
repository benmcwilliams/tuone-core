import json
from collections import defaultdict
from typing import List, Dict, Any
from functions.utils_duplicates import load_json

def update_duplicates(new_duplicates_path: str, duplicates_path: str) -> None:
    """
    This function reads multiple JSON files containing duplicate data, merges their contents into a single,
    consistent output, and saves this merged data back to one of the original files.

    Parameters:
    - new_duplicates_path: The file path of the new duplicates JSON file to be merged.
    - duplicates_path: The file path of the existing duplicates JSON file that will be updated with the merged data.

    Inner Function - merge_json_files:
    - This function takes a list of file paths as input and merges the JSON data from these files.
    - It uses a defaultdict to collect values for each key, ensuring that duplicate values are avoided during the merging process.

    Merging Process:
    - For each file in the provided list, it loads the JSON data and appends values to the corresponding keys in the merged dictionary, ensuring that no duplicates are added.

    """

    #### reads in all the duplicate JSONs and merges them into one consistent output 

    def merge_json_files(file_list: List[str]) -> Dict[str, List[str]]:
        merged_data = defaultdict(list)  # Use defaultdict to automatically handle new keys

        for file_name in file_list:
            data = load_json(file_name)
            for key, value in data.items():
                # Append the new values to the existing list, avoiding duplicates
                merged_data[key].extend(val for val in value if val not in merged_data[key])

        # Convert defaultdict back to regular dict for saving or returning
        return dict(merged_data)

    file_list = [duplicates_path, new_duplicates_path] 
    merged_dict = merge_json_files(file_list)

    # Save the merged dictionary to a new JSON file (if needed)
    with open(duplicates_path, 'w') as output_file:
        print(f"Saving master duplicates to {duplicates_path}")
        json.dump(merged_dict, output_file, indent=4)