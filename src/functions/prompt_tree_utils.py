import json

def get_technology_from_project_id(project_id):
    # Load the tech dictionary from the JSON file
    with open('src/inputs/tech_dict.json') as f:
        tech_dict = json.load(f)
    
    # Reverse the tech dictionary
    reversed_tech_dict = {v: k for k, v in tech_dict.items()}
    
    # Extract the last two digits from the project ID using indexing
    tech_code = project_id[-2:]
    
    # Return the corresponding technology
    return reversed_tech_dict.get(tech_code, "Unknown technology")

# Example usage
project_id = "ITA-01352-01424_04"
technology = get_technology_from_project_id(project_id)
print(technology)  # Output: battery