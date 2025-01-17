import json
from src.config.config_paths import PROMPT_TREE_TECHNOLOGY, PROMPT_TREE_ECONOMIC
from src.config.config_paths import TECHNOLOGY_JSON, COMPONENT_JSON, ECONOMIC_JSON
from src.config.config_prompt_tree import get_component_dict_value, tech_dict
from functions.prompt_tree_utils import get_technology_from_project_id
from functions.general import read_prompt_from_file_only, read_prompt_from_file, load_json, save_json_to_file
from functions.component_tree import check_component
from functions.openai import query_model

# files where model outputs are stored, each file is a dictionary with projectID_{kwargs} as key
tech_values = load_json(TECHNOLOGY_JSON)
economic_values = load_json(ECONOMIC_JSON)
component_values = load_json(COMPONENT_JSON)

def return_tech_economic(client, project_text, projectID, company, location):

    # prompt for technology
    technology_system_prompt = read_prompt_from_file_only(PROMPT_TREE_TECHNOLOGY)
    technology_raw = query_model(client, "gpt-4o-mini", technology_system_prompt, project_text)
    technologies = json.loads(technology_raw)

    for tech in technologies:

        print(f"- - - Technology identified as: {tech}")

        # add tech to tech_values with a projectID_techID key
        tech_values[projectID + "_" + tech_dict[tech]] = tech  

        # Prompt for economic branch (deployment or manufacturing)
        economic_system_prompt = read_prompt_from_file(PROMPT_TREE_ECONOMIC, company=company, location=location, tech=tech)
        economic = query_model(client, "gpt-4o-mini", economic_system_prompt, project_text)
        economic_values[projectID + "_" + tech_dict[tech]] = economic

        print(f"- - - For {tech}, economic branch identified as: {economic}")

    # Save tech and economicvalues to file
    save_json_to_file(tech_values, TECHNOLOGY_JSON)
    save_json_to_file(economic_values, ECONOMIC_JSON)

