# utils.py

from functions.openai import return_specific_value
import pickle
import json

def load_mappings():
    with open('src/mappings/company_to_companyID.pkl', 'rb') as f:
        company_to_companyID = pickle.load(f)

    with open('src/mappings/location_to_locationID.pkl', 'rb') as f:
        location_to_locationID = pickle.load(f)

    companyID_to_company = {v: k for k, v in company_to_companyID.items()}
    locationID_to_location = {v: k for k, v in location_to_locationID.items()}

    return companyID_to_company, locationID_to_location

def build_article_lookup_dict(articles):
    """
    Takes a list of article records (each a dict) and
    returns a dictionary keyed by the article's 'meta["ID"]' as a string.

    Example record structure in 'articles':
    {
      "title": "Mitsubishi Chemical expands production capacities",
      "paragraphs": {...},
      "meta": {
        "ID": "1100001",
        "date": "04-12-2017",
        "url": "..."
      }
    }

    """
    lookup_dict = {}
    for record in articles:
        # record["meta"]["ID"] should exist if your JSONL follows the posted structure
        article_id_raw = record["meta"]["ID"]  
        # Force string in case it's numeric in the JSON
        article_id_str = str(article_id_raw)
        lookup_dict[article_id_str] = record
    return lookup_dict


def check_component(tech, client, text_factsheet, prompts):
    if tech.lower() == 'battery':
        return return_specific_value(client, text_factsheet, prompts['component_battery'])
    elif tech.lower() == 'zero_emission_vehicle':
        return return_specific_value(client, text_factsheet, prompts['component_vehicle'])
    elif tech.lower() == 'solar':
        return return_specific_value(client, text_factsheet, prompts['component_solar'])
    elif tech.lower() == 'hydrogen':
        return return_specific_value(client, text_factsheet, prompts['component_hydrogen'])
    elif tech.lower() == 'wind':
        return return_specific_value(client, text_factsheet, prompts['component_wind'])
    else:
        return 'Unknown Component'


def process_expansion_phases(client, text_factsheet, prompts):
    # Extract key information for expansions
    investment_value = return_specific_value(client, text_factsheet, prompts['expansion_investments'], model='ft:gpt-4o-mini-2024-07-18:personal:multiple-return-values:AJKRBH3e')
    capacity = return_specific_value(client, text_factsheet, prompts['expansion_capacities'], model='ft:gpt-4o-mini-2024-07-18:personal:multiple-return-capacities:AJLPXkDZ')
    status = return_specific_value(client, text_factsheet, prompts['expansion_statuses'], model='ft:gpt-4o-mini-2024-07-18:personal:multiple-return-statuses:AJKvbgjo')
    dt_announce = return_specific_value(client, text_factsheet, prompts['expansion_dates_announce'], model='ft:gpt-4o-mini-2024-07-18:personal:multiple-return-dt-announce:AJNCwI4G')
    
    dt_construct = 'N/A'
    dt_operation = 'N/A'
    
    if "actual" in status or "operational" in status:
        print("Actual or operational expansion detected")
        dt_construct = return_specific_value(client, text_factsheet, prompts['expansion_dates_construct'], model='ft:gpt-4o-mini-2024-07-18:personal:multiple-return-dt-construct:AJOfYnaA')
    
    if "operational" in status:
        print("Operational expansion detected")
        dt_operation = return_specific_value(client, text_factsheet, prompts['expansion_dates_operate'])
    
    return investment_value, capacity, status, dt_announce, dt_construct, dt_operation

def process_unique_phase(client, text_factsheet, prompts):
    # Extract key information for unique phase
    investment_value = return_specific_value(client, text_factsheet, prompts['return_investment'], model = 'ft:gpt-4o-mini-2024-07-18:personal:return-value:AJKGYiKy')

    capacity = return_specific_value(client, text_factsheet, prompts['return_capacity'], model = 'ft:gpt-4o-mini-2024-07-18:personal:return-capacity:AJLE8MZB')
    status = return_specific_value(client, text_factsheet, prompts['return_status'], model = 'ft:gpt-4o-mini-2024-07-18:personal:return-status:AJKjY2fz')
    dt_announce = return_specific_value(client, text_factsheet, prompts['return_date_announce'], model = 'ft:gpt-4o-mini-2024-07-18:personal:return-dt-announce:AJMziNNI')

    dt_construct = 'N/A'
    dt_operation = 'N/A'

    if status.lower() in ['actual', 'operational']:
        dt_construct = return_specific_value(client, text_factsheet, prompts['return_date_construct'], model = 'ft:gpt-4o-mini-2024-07-18:personal:return-dt-construct:AJNVZhZi')

    if status.lower() in ['operational']:
        dt_operation = return_specific_value(client, text_factsheet, prompts['return_date_operate'], model = 'ft:gpt-4o-mini-2024-07-18:personal:return-dt-operation:AJNoAOsB')

    return investment_value, capacity, status, dt_announce, dt_construct, dt_operation
    
def safe_convert_to_int(value, default="NA"):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
    
def load_sources_dict(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return {item['two_digit_ID']: item['source'] for item in data['sources']}

def get_source_by_id(source_dict, two_digit_ID):
    return source_dict.get(two_digit_ID, "Source not found")


def get_date():
    return None