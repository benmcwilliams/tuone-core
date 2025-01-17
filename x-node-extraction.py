from openai import OpenAI
import os
import json
from src.config.config_paths import PROJECTS_CHRONOLOGICAL, PROCESSED_NODES, SUMMARIES_EVOLUTIONARY_CONTRASTIVE
from src.config.config_paths import TECHNOLOGY_JSON, ECONOMIC_JSON, COMPONENT_JSON, PHASE_JSON, PHASE_STATUS_JSON, PHASE_DT_ANNOUNCE_JSON, PHASE_DT_ACTUAL_JSON, PHASE_DT_OPERATIONAL_JSON, PHASE_DT_CANCEL_JSON, PHASE_INVESTMENT_VALUE_JSON, PHASE_CAPACITY_JSON, PHASE_JOBS_JSON
from src.config.config_paths import PROMPT_TREE_TECHNOLOGY, PROMPT_TREE_ECONOMIC, PROMPT_TREE_PHASES
from src.config.config_paths import PROMPT_PHASE_STATUS, PROMPT_PHASE_DT_ANNOUNCE, PROMPT_PHASE_DT_ACTUAL, PROMPT_PHASE_DT_OPERATIONAL, PROMPT_PHASE_DT_CANCEL, PROMPT_PHASE_INVESTMENT_VALUE, PROMPT_PHASE_CAPACITY, PROMPT_PHASE_JOBS
from src.config.config_prompt_tree import get_component_dict_value, tech_dict, phase_dict
from functions.general import project_needs_update, load_json, read_prompt_from_file_only, read_prompt_from_file, save_json_to_file
from functions.utils import load_mappings
from functions.openai import query_model, clean_model_output
from functions.component_tree import check_component

# initialise openAI client
openAI_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(
    api_key=openAI_api_key,
  )

# load company and location mappings
companyID_to_company, locationID_to_location = load_mappings()

# load dictionaries where model outputs are stored
tech_values = load_json(TECHNOLOGY_JSON)
economic_values = load_json(ECONOMIC_JSON)
component_values = load_json(COMPONENT_JSON)
phase_values = load_json(PHASE_JSON)

# load dictionaries where phase-level model outputs are stored
phase_status_values = load_json(PHASE_STATUS_JSON)
phase_dt_announce_values = load_json(PHASE_DT_ANNOUNCE_JSON)
phase_dt_actual_values = load_json(PHASE_DT_ACTUAL_JSON)
phase_dt_operational_values = load_json(PHASE_DT_OPERATIONAL_JSON)
phase_dt_cancel_values = load_json(PHASE_DT_CANCEL_JSON)
phase_investment_value_values = load_json(PHASE_INVESTMENT_VALUE_JSON)
phase_capacity_values = load_json(PHASE_CAPACITY_JSON)
phase_jobs_values = load_json(PHASE_JOBS_JSON)

# load projects
with open(PROJECTS_CHRONOLOGICAL, 'r') as file:
    projects = json.load(file)

# load (or create) processed_projects dictionary
if os.path.exists(PROCESSED_NODES):
    with open(PROCESSED_NODES, 'r') as file:
        projects_processed_data = json.load(file)
else:
    projects_processed_data = {}

for projectID, articleIDs in projects.items():

    # project level variables

    country = projectID[:3]
    location = locationID_to_location.get(projectID[4:9], 'Unknown Location')
    company = companyID_to_company.get(projectID[10:15], 'Unknown Company')

    needs_update, update_reason = project_needs_update(projectID, articleIDs, projects_processed_data)

    if not needs_update:
        print(f" - Skipping project {projectID} (already processed and up to date).")
        continue

    print(f"## Processing project: {company}, {location}, {country}. Reason: {update_reason}. ID: {projectID}")

    # load the project summary
    master_summary_path = f'{SUMMARIES_EVOLUTIONARY_CONTRASTIVE}/{projectID}.txt'
    with open(master_summary_path, 'r') as file:
        project_summary = file.read()

    # prompt for technology extraction
    technology_system_prompt = read_prompt_from_file_only(PROMPT_TREE_TECHNOLOGY)
    technology_raw = query_model(client, "gpt-4o-mini", technology_system_prompt, project_summary)
    technologies = json.loads(technology_raw)

    for tech in technologies:

        # add tech to tech_values with a projectID_techID key
        tech_values[projectID + "_" + tech_dict[tech]] = tech  
        print(f"- - Technology identified as: {tech}")

        # prompt for economic branch (deployment or manufacturing)
        economic_system_prompt = read_prompt_from_file(PROMPT_TREE_ECONOMIC, company=company, location=location, tech=tech)
        economic = query_model(client, "gpt-4o-mini", economic_system_prompt, project_summary)
        economic_values[projectID + "_" + tech_dict[tech]] = economic
        print(f"- - - For {tech}, economic branch identified as: {economic}")

        ## identify component as deployment
        if economic == "deployment":
            component = "deployment"
            component_code = get_component_dict_value(tech, component)
            print(component_code)
            component_values[projectID + "_" + tech_dict[tech] + "_" + component_code] = component

            # prompt for number of phases
            phase_system_prompt = read_prompt_from_file(PROMPT_TREE_PHASES, company=company, location=location, country=country, tech=tech, component=component)
            num_phase = query_model(client, "gpt-4o-mini", phase_system_prompt, project_summary)

            # add num_phase to phase_values with a projectID_techID_componentID key
            phase_values[projectID + "_" + tech_dict[tech] + "_" + component_code] = num_phase
            print(f"- - - For {tech}, {component}, number of investement phases detected: {num_phase}")

            # loop through each phase and prompt for phase-level information
            num_phase_int = int(num_phase)
            for phase in range(num_phase_int):
                phase_code = f"{phase:02}"
                phase_text = phase_dict[phase_code]
                print(f"- - - - - Phase: {phase_code}")
                print(f"- - - - - Phase: {phase_text}")

                # return status
                status_system_prompt = read_prompt_from_file(PROMPT_PHASE_STATUS, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text)
                status = query_model(client, "gpt-4o-mini", status_system_prompt, project_summary)
                phase_status_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = status   
                print(f"- - - - - - Status: {status}")

                # return dt_announce
                dt_announce_system_prompt = read_prompt_from_file(PROMPT_PHASE_DT_ANNOUNCE, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text, status=status)
                dt_announce = query_model(client, "gpt-4o-mini", dt_announce_system_prompt, project_summary)
                phase_dt_announce_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = dt_announce
                print(f"- - - - - - DT Announce: {dt_announce}")

                # if status == actual or == operational then query for dt_actual
                if status == "actual" or status == "operational":
                    dt_actual_system_prompt = read_prompt_from_file(PROMPT_PHASE_DT_ACTUAL, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text, status=status)
                    dt_actual = query_model(client, "gpt-4o-mini", dt_actual_system_prompt, project_summary)
                    phase_dt_actual_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = dt_actual
                    print(f"- - - - - - DT Actual: {dt_actual}")

                else:
                    phase_dt_actual_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = "NA"

                # if status == operational then query for dt_operational
                if status == "operational":
                    dt_operational_system_prompt = read_prompt_from_file(PROMPT_PHASE_DT_OPERATIONAL, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text, status=status)
                    dt_operational = query_model(client, "gpt-4o-mini", dt_operational_system_prompt, project_summary)
                    phase_dt_operational_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = dt_operational
                    print(f"- - - - - - DT Operational: {dt_operational}")

                else:
                    phase_dt_operational_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = "NA"

                # if status == cancelled then query for dt_cancel
                if status == "cancelled":
                    dt_cancel_system_prompt = read_prompt_from_file(PROMPT_PHASE_DT_CANCEL, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text, status=status)
                    dt_cancel = query_model(client, "gpt-4o-mini", dt_cancel_system_prompt, project_summary)
                    phase_dt_cancel_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = dt_cancel
                    print(f"- - - - - - DT Cancel: {dt_cancel}")

                else:
                    phase_dt_cancel_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = "NA"

                # return investment_value
                investment_value_system_prompt = read_prompt_from_file(PROMPT_PHASE_INVESTMENT_VALUE, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text, status=status)
                investment_value = query_model(client, "gpt-4o-mini", investment_value_system_prompt, project_summary)
                phase_investment_value_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = investment_value
                print(f"- - - - - - Investment Value: {investment_value}")

                # return capacity
                capacity_system_prompt = read_prompt_from_file(PROMPT_PHASE_CAPACITY, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text, status=status)
                capacity = query_model(client, "gpt-4o-mini", capacity_system_prompt, project_summary)
                phase_capacity_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = capacity
                print(f"- - - - - - Capacity: {capacity}")

                # return jobs
                jobs_system_prompt = read_prompt_from_file(PROMPT_PHASE_JOBS, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text, status=status)
                jobs = query_model(client, "gpt-4o-mini", jobs_system_prompt, project_summary)
                phase_jobs_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = jobs
                print(f"- - - - - - Jobs: {jobs}")

        ## identify component as manufacturing
        elif economic == "manufacturing":
            raw_component = check_component(tech, client, project_summary)
            print(f"Raw component output: {raw_component}")
            raw_component = clean_model_output(raw_component)

            # if model is unable to identify component, set component to "Unable to identify component"
            if raw_component == "NA":
                component = "Unable to identify component"
                component_code = get_component_dict_value(tech, raw_component)
                component_values[projectID + "_" + tech_dict[tech] + "_" + component_code] = component
                print(f"- - - - Unable to identify component")

                # set phase to NA marker (indicating that a component was not identified)
                phase_values[projectID + "_" + tech_dict[tech] + "_" + component_code] = component

            # if model is able to identify components 
            else:
                components = json.loads(raw_component)

                # loop through; add each component to component_values; and process further
                for component in components:

                    # add component to component_values
                    component_code = get_component_dict_value(tech, component)
                    component_values[projectID + "_" + tech_dict[tech] + "_" + component_code] = component
                    print(f"- - - - Component identified as: {component}")

                    # prompt for number of phases
                    phase_system_prompt = read_prompt_from_file(PROMPT_TREE_PHASES, company=company, location=location, country=country, tech=tech, component=component)
                    num_phase = query_model(client, "gpt-4o-mini", phase_system_prompt, project_summary)
                    phase_values[projectID + "_" + tech_dict[tech] + "_" + component_code] = num_phase

                    # loop through each phase and prompt for phase-level information
                    num_phase_int = int(num_phase)
                    for phase in range(num_phase_int):
                        phase_code = f"{phase:02}"
                        phase_text = phase_dict[phase_code]
                        print(f"- - - - - Phase: {phase_code}")
                        print(f"- - - - - Phase: {phase_text}")

                        # return status
                        status_system_prompt = read_prompt_from_file(PROMPT_PHASE_STATUS, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text)
                        status = query_model(client, "gpt-4o-mini", status_system_prompt, project_summary)
                        phase_status_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = status
                        print(f"- - - - - - Status: {status}")

                        # return dt_announce
                        dt_announce_system_prompt = read_prompt_from_file(PROMPT_PHASE_DT_ANNOUNCE, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text, status=status)
                        dt_announce = query_model(client, "gpt-4o-mini", dt_announce_system_prompt, project_summary)
                        phase_dt_announce_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = dt_announce
                        print(f"- - - - - - DT Announce: {dt_announce}")

                        # if status == actual or == operational then query for dt_actual
                        if status == "actual" or status == "operational":
                            dt_actual_system_prompt = read_prompt_from_file(PROMPT_PHASE_DT_ACTUAL, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text, status=status)
                            dt_actual = query_model(client, "gpt-4o-mini", dt_actual_system_prompt, project_summary)
                            phase_dt_actual_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = dt_actual
                            print(f"- - - - - - DT Actual: {dt_actual}")

                        else:
                            phase_dt_actual_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = "NA"

                        # if status == operational then query for dt_operational
                        if status == "operational":
                            dt_operational_system_prompt = read_prompt_from_file(PROMPT_PHASE_DT_OPERATIONAL, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text, status=status)
                            dt_operational = query_model(client, "gpt-4o-mini", dt_operational_system_prompt, project_summary)
                            phase_dt_operational_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = dt_operational
                            print(f"- - - - - - DT Operational: {dt_operational}")

                        else:
                            phase_dt_operational_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = "NA"

                        # if status == cancelled then query for dt_cancel
                        if status == "cancelled":
                            dt_cancel_system_prompt = read_prompt_from_file(PROMPT_PHASE_DT_CANCEL, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text, status=status)
                            dt_cancel = query_model(client, "gpt-4o-mini", dt_cancel_system_prompt, project_summary)
                            phase_dt_cancel_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = dt_cancel
                            print(f"- - - - - - DT Cancel: {dt_cancel}")

                        else:
                            phase_dt_cancel_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = "NA"

                        # return investment_value
                        investment_value_system_prompt = read_prompt_from_file(PROMPT_PHASE_INVESTMENT_VALUE, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text, status=status)
                        investment_value = query_model(client, "gpt-4o-mini", investment_value_system_prompt, project_summary)
                        phase_investment_value_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = investment_value
                        print(f"- - - - - - Investment Value: {investment_value}")

                        # return capacity
                        capacity_system_prompt = read_prompt_from_file(PROMPT_PHASE_CAPACITY, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text, status=status)
                        capacity = query_model(client, "gpt-4o-mini", capacity_system_prompt, project_summary)
                        phase_capacity_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = capacity
                        print(f"- - - - - - Capacity: {capacity}")

                        # return jobs
                        jobs_system_prompt = read_prompt_from_file(PROMPT_PHASE_JOBS, company=company, location=location, country=country, tech=tech, component=component, phase=phase_text, status=status)
                        jobs = query_model(client, "gpt-4o-mini", jobs_system_prompt, project_summary)
                        phase_jobs_values[projectID + "_" + tech_dict[tech] + "_" + component_code + "_" + phase_code] = jobs
                        print(f"- - - - - - Jobs: {jobs}")

        else:
            print(f" - - - !!! Warning: economic branch not identified as deployment or manufacturing for {tech}.")

    # Save tech and economic values to file
    save_json_to_file(tech_values, TECHNOLOGY_JSON)
    save_json_to_file(economic_values, ECONOMIC_JSON)
    save_json_to_file(component_values, COMPONENT_JSON)
    save_json_to_file(phase_values, PHASE_JSON)
    save_json_to_file(phase_status_values, PHASE_STATUS_JSON)
    save_json_to_file(phase_dt_announce_values, PHASE_DT_ANNOUNCE_JSON)
    save_json_to_file(phase_dt_actual_values, PHASE_DT_ACTUAL_JSON)
    save_json_to_file(phase_dt_operational_values, PHASE_DT_OPERATIONAL_JSON)
    save_json_to_file(phase_dt_cancel_values, PHASE_DT_CANCEL_JSON)
    save_json_to_file(phase_investment_value_values, PHASE_INVESTMENT_VALUE_JSON)
    save_json_to_file(phase_capacity_values, PHASE_CAPACITY_JSON)
    save_json_to_file(phase_jobs_values, PHASE_JOBS_JSON)

    # Update processed projects data with any new projectIDs or article IDs that have just been processed
    projects_processed_data[projectID] = [int(article_id) for article_id in articleIDs]

    with open(PROCESSED_NODES, 'w') as file:
        json.dump(projects_processed_data, file, indent=4)