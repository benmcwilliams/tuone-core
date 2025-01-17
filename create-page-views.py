import json
from src.config.config_paths import PROJECTS_CHRONOLOGICAL, OBSIDIAN_VAULT_PROJECTS, OBSIDIAN_VAULT_COMPANIES, OBSIDIAN_VAULT_LOCATIONS
from src.config.config_paths import SUMMARIES_MASTER
from functions.utils import load_mappings
from functions.obsidian import get_phases_for_project
import os

#CONFIGURATION
os.makedirs(OBSIDIAN_VAULT_PROJECTS, exist_ok=True)
os.makedirs(OBSIDIAN_VAULT_COMPANIES, exist_ok=True)
os.makedirs(OBSIDIAN_VAULT_LOCATIONS, exist_ok=True)

#load company and location mappings
companyID_to_company, locationID_to_location = load_mappings()

#read in project-articles mapping
with open(PROJECTS_CHRONOLOGICAL, 'r') as file:
    projects = json.load(file)

#create project specific pages with a dataview list of all phases present in the project
for projectID, articleIDs in projects.items():

    country = projectID[:3]
    location = locationID_to_location.get(projectID[4:9], 'Unknown Location')
    company = companyID_to_company.get(projectID[10:15], 'Unknown Company')
    company = company.replace(' ', '-')
    company = company.replace(':', '-')
    company = company.replace('"', '')
    location = location.replace(' ', '-')
    location = location.replace(':', '-')

    #return the phases associated with a given project
    phase_ids = get_phases_for_project(projectID)

    #construct output filename and filepath
    filename = f"{company}-{location}.md"
    filepath = os.path.join(OBSIDIAN_VAULT_PROJECTS, filename)
    
    #create the file
    with open(filepath, 'w') as file:
        dataview_code = f"table location, company, tech, component, status, phase, capacity, investment_value, dt_announce\nfrom \"phases\"\nwhere contains(file.name, \"{projectID}\") and reject-phase = false\nsort location, company asc"
        file.write("```dataview\n")  # Start Dataview block
        file.write(dataview_code)  # Embed the Dataview code
        file.write("\n```\n")  # End Dataview block

#create company-specific pages with a dataview list of all phases present in the company
company_pages = {}

# First, group all phases by company
for projectID, articleIDs in projects.items():
    company = companyID_to_company.get(projectID[10:15], 'Unknown Company')
    company = company.replace(' ', '-')
    company = company.replace(':', '-')
    
    # If this company isn't in our dict yet, initialize it
    if company not in company_pages:
        company_pages[company] = []
    
    # Add this project's ID to the company's list
    company_pages[company].append(projectID)

# Create a page for each company
for company, projectIDs in company_pages.items():
    filename = f"{company}.md"
    filepath = os.path.join(OBSIDIAN_VAULT_COMPANIES, filename)
    
    with open(filepath, 'w') as file:
        # Create a dataview query that will show all phases for this company
        dataview_code = f"table location, company, tech, component, status, phase, capacity, investment_value, dt_announce\nfrom \"phases\"\nwhere reject-phase = false and company = \"{company.replace('-', ' ')}\"\nsort location, dt_announce desc"
        file.write("```dataview\n")
        file.write(dataview_code)
        file.write("\n```\n")

# Create location-specific pages
location_pages = {}

# First, group all phases by location
for projectID, articleIDs in projects.items():
    location = locationID_to_location.get(projectID[4:9], 'Unknown Location')
    location = location.replace(' ', '-')
    location = location.replace(':', '-')
    
    # If this location isn't in our dict yet, initialize it
    if location not in location_pages:
        location_pages[location] = []
    
    # Add this project's ID to the location's list
    location_pages[location].append(projectID)

# Create a page for each location
for location, projectIDs in location_pages.items():
    filename = f"{location}.md"
    filepath = os.path.join(OBSIDIAN_VAULT_LOCATIONS, filename)
    
    with open(filepath, 'w') as file:
        # Create a dataview query that will show all phases for this location
        dataview_code = f"table company, tech, component, status, capacity, investment_value, dt_announce\nfrom \"phases\"\nwhere reject-phase = false and location = \"{location.replace('-', ' ')}\"\nsort company, dt_announce desc"
        file.write("```dataview\n")
        file.write(dataview_code)
        file.write("\n```\n")