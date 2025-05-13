from functions.openai import query_model
from src.config.config_paths import PROMPT_COMPONENT_BATTERY, PROMPT_COMPONENT_SOLAR, PROMPT_COMPONENT_VEHICLE, PROMPT_COMPONENT_WIND
from src.config.config_paths import PROMPT_COMPONENT_HYDROGEN, PROMPT_COMPONENT_NUCLEAR, PROMPT_COMPONENT_GEOTHERMAL, PROMPT_COMPONENT_HYDRO, PROMPT_COMPONENT_BIOMASS
from functions.general import read_prompt_from_file_only

def check_component(tech, client, project_text):
    if tech.lower() == 'battery':
        system_prompt = read_prompt_from_file_only(PROMPT_COMPONENT_BATTERY)
        return query_model(client, "gpt-4o-mini", system_prompt, project_text)
    elif tech.lower() == 'solar':
        system_prompt = read_prompt_from_file_only(PROMPT_COMPONENT_SOLAR)
        return query_model(client, "gpt-4o-mini", system_prompt, project_text)
    elif tech.lower() == 'vehicle':
        system_prompt = read_prompt_from_file_only(PROMPT_COMPONENT_VEHICLE)
        return query_model(client, "gpt-4o-mini", system_prompt, project_text)
    elif tech.lower() == 'hydrogen':
        system_prompt = read_prompt_from_file_only(PROMPT_COMPONENT_HYDROGEN)
        return query_model(client, "gpt-4o-mini", system_prompt, project_text)
    elif tech.lower() == 'wind':
        system_prompt = read_prompt_from_file_only(PROMPT_COMPONENT_WIND)
        return query_model(client, "gpt-4o-mini", system_prompt, project_text)
    elif tech.lower() == 'nuclear':
        system_prompt = read_prompt_from_file_only(PROMPT_COMPONENT_NUCLEAR)
        return query_model(client, "gpt-4o-mini", system_prompt, project_text)
    elif tech.lower() == 'geothermal':
        system_prompt = read_prompt_from_file_only(PROMPT_COMPONENT_GEOTHERMAL)
        return query_model(client, "gpt-4o-mini", system_prompt, project_text)
    elif tech.lower() == 'hydroelectric':
        system_prompt = read_prompt_from_file_only(PROMPT_COMPONENT_HYDRO)
        return query_model(client, "gpt-4o-mini", system_prompt, project_text)
    elif tech.lower() == 'biomass':
        system_prompt = read_prompt_from_file_only(PROMPT_COMPONENT_BIOMASS)
        return query_model(client, "gpt-4o-mini", system_prompt, project_text)
    else:
        return 'Unknown Component'
