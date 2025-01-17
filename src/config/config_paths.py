# defined originally for update_duplicates.py
METADATA_PATH = 'src/models_metadata/metadata_validated.json'
DUPLICATES_PATH = 'src/inputs/duplicates.json'
NEW_DUPLICATES_PATH = 'src/inputs/validated_duplicates.json'

#defined originally for v-unique-projects.py
PROJECT_ARTICLE_LISTS = "src/article_project_lists"
DUPLICATE_PROJECTS_PATH = 'src/inputs/duplicates.json'
RECOGNISED_PROJECTS_JSON = 'src/outputs/project_collections/projects_recognised.json'
RECOGNISED_PROJECTS_CSV = 'src/projects_recognised.csv'

# article dictionaries
ARTICLE_ID_DATE_JSONL = 'src/outputs/article_dictionaries/article_ID_date.jsonl'
ARTICLE_ID_TITLE_JSONL = 'src/outputs/article_dictionaries/article_ID_title.jsonl'
ARTICLE_ID_URL_JSONL = 'src/outputs/article_dictionaries/article_ID_url.jsonl'

# project collections
PROJECTS_CHRONOLOGICAL = 'src/outputs/project_collections/chronological.json'

# prompts
PROMPT_SUMMARY_ORIGINAL = 'prompts/summaries/original.txt'
PROMPT_SUMMARY_EVOLUTIONARY = 'prompts/summaries/evolutionary.txt'
PROMPT_SUMMARY_COMPRESSIVE = 'prompts/summaries/compressive.txt'
PROMPT_SUMMARY_QUALITY = 'prompts/summaries/quality.txt'
PROMPT_SUMMARY_CONTRASTIVE = 'prompts/summaries/contrastive.txt'

#google-cloud-database
GS_ARTICLE_DATABASE = "gs://tuone-article-database/article_database.jsonl"

#summaries
SUMMARIES_EVOLUTIONARY = 'src/outputs/summaries/evolutionary'
SUMMARIES_CONTRASTIVE = 'src/outputs/summaries/contrastive'
SUMMARIES_QUALITY = 'src/outputs/summaries/quality'
SUMMARIES_COMPRESSIVE = 'src/outputs/summaries/compressive'
SUMMARIES_MASTER = 'src/outputs/summaries/master'
SUMMARIES_EVOLUTIONARY_CONTRASTIVE = 'src/outputs/summaries/evolutionary_contrastive'

#tracking processed projects
PROCESSED_NODES = 'src/outputs/processed/nodes.json'
PROCESSED_SUMMARIES_ROOT = 'src/outputs/processed/summaries'
PROCESSED_SUMMARIES_MERGED = 'src/outputs/processed/summaries_merged.json'

#prompt tree
PROMPT_TREE_TECHNOLOGY = 'prompts/prompt_tree/technology.txt'
PROMPT_TREE_ECONOMIC = 'prompts/prompt_tree/deployment-manufacturing.txt'
PROMPT_TREE_PHASES = 'prompts/prompt_tree/phases.txt'

#prompts for components
PROMPT_COMPONENT_BATTERY = 'prompts/prompt_tree/components/battery.txt'
PROMPT_COMPONENT_SOLAR = 'prompts/prompt_tree/components/solar.txt'
PROMPT_COMPONENT_VEHICLE = 'prompts/prompt_tree/components/vehicle.txt'
PROMPT_COMPONENT_HYDROGEN = 'prompts/prompt_tree/components/hydrogen.txt'
PROMPT_COMPONENT_WIND = 'prompts/prompt_tree/components/wind.txt'
PROMPT_COMPONENT_GEOTHERMAL = 'prompts/prompt_tree/components/geothermal.txt'
PROMPT_COMPONENT_NUCLEAR = 'prompts/prompt_tree/components/nuclear.txt'
PROMPT_COMPONENT_HYDRO = 'prompts/prompt_tree/components/hydroelectric.txt'
PROMPT_COMPONENT_BIOMASS = 'prompts/prompt_tree/components/biomass.txt'

#phase-level prompts
PROMPT_PHASE_STATUS = 'prompts/prompt_tree/phase_level/status.txt'
PROMPT_PHASE_DT_ANNOUNCE = 'prompts/prompt_tree/phase_level/dt_announce.txt'
PROMPT_PHASE_DT_ACTUAL = 'prompts/prompt_tree/phase_level/dt_actual.txt'
PROMPT_PHASE_DT_OPERATIONAL = 'prompts/prompt_tree/phase_level/dt_operational.txt'
PROMPT_PHASE_DT_CANCEL = 'prompts/prompt_tree/phase_level/dt_cancel.txt'
PROMPT_PHASE_INVESTMENT_VALUE = 'prompts/prompt_tree/phase_level/investment_value.txt'
PROMPT_PHASE_CAPACITY = 'prompts/prompt_tree/phase_level/capacity.txt'
PROMPT_PHASE_JOBS = 'prompts/prompt_tree/phase_level/jobs.txt'

#model outputs
TECHNOLOGY_JSON = 'src/outputs/model/technology.json'
ECONOMIC_JSON = 'src/outputs/model/economic.json'
COMPONENT_JSON = 'src/outputs/model/component.json'
PHASE_JSON = 'src/outputs/model/phase.json'

#phase-level model outputs
PHASE_STATUS_JSON = 'src/outputs/model/phase_level/status.json'
PHASE_DT_ANNOUNCE_JSON = 'src/outputs/model/phase_level/dt_announce.json'
PHASE_DT_ACTUAL_JSON = 'src/outputs/model/phase_level/dt_actual.json'
PHASE_DT_OPERATIONAL_JSON = 'src/outputs/model/phase_level/dt_operational.json'
PHASE_DT_CANCEL_JSON = 'src/outputs/model/phase_level/dt_cancel.json'
PHASE_INVESTMENT_VALUE_JSON = 'src/outputs/model/phase_level/investment_value.json'
PHASE_CAPACITY_JSON = 'src/outputs/model/phase_level/capacity.json'
PHASE_JOBS_JSON = 'src/outputs/model/phase_level/jobs.json'

# database-level dictionaries
TECH_DICT_JSON = 'src/inputs/tech_dict.json'
PHASE_DICT_JSON = 'src/inputs/phase_dict.json'
SOLAR_COMPONENT_DICT_JSON = 'src/inputs/component_dicts/solar.json'
WIND_COMPONENT_DICT_JSON = 'src/inputs/component_dicts/wind.json'
BATTERY_COMPONENT_DICT_JSON = 'src/inputs/component_dicts/battery.json'
GEOTHERMAL_COMPONENT_DICT_JSON = 'src/inputs/component_dicts/geothermal.json'
HYDROELECTRIC_COMPONENT_DICT_JSON = 'src/inputs/component_dicts/hydroelectric.json'
HYDROGEN_COMPONENT_DICT_JSON = 'src/inputs/component_dicts/hydrogen.json'
NUCLEAR_COMPONENT_DICT_JSON = 'src/inputs/component_dicts/nuclear.json'
VEHICLE_COMPONENT_DICT_JSON = 'src/inputs/component_dicts/vehicle.json'
BIOMASS_COMPONENT_DICT_JSON = 'src/inputs/component_dicts/biomass.json'

# vault
OBSIDIAN_VAULT_PROJECTS = 'vault/src/projects'
OBSIDIAN_VAULT_PHASE = 'vault/src/phases'
OBSIDIAN_VAULT_COMPANIES = 'vault/src/companies'
OBSIDIAN_VAULT_LOCATIONS = 'vault/src/locations'
