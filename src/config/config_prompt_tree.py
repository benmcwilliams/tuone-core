from src.config.config_paths import TECH_DICT_JSON, SOLAR_COMPONENT_DICT_JSON, WIND_COMPONENT_DICT_JSON, BATTERY_COMPONENT_DICT_JSON, GEOTHERMAL_COMPONENT_DICT_JSON, HYDROELECTRIC_COMPONENT_DICT_JSON, HYDROGEN_COMPONENT_DICT_JSON, NUCLEAR_COMPONENT_DICT_JSON, VEHICLE_COMPONENT_DICT_JSON, BIOMASS_COMPONENT_DICT_JSON, PHASE_DICT_JSON
from functions.general import load_json

# define phase dictionary
phase_dict = load_json(PHASE_DICT_JSON)

# load technology dictionary
tech_dict = load_json(TECH_DICT_JSON)

# load component dictionaries
solar_component_dict = load_json(SOLAR_COMPONENT_DICT_JSON)
wind_component_dict = load_json(WIND_COMPONENT_DICT_JSON)
battery_component_dict = load_json(BATTERY_COMPONENT_DICT_JSON)
geothermal_component_dict = load_json(GEOTHERMAL_COMPONENT_DICT_JSON)
hydroelectric_component_dict = load_json(HYDROELECTRIC_COMPONENT_DICT_JSON)
hydrogen_component_dict = load_json(HYDROGEN_COMPONENT_DICT_JSON)
nuclear_component_dict = load_json(NUCLEAR_COMPONENT_DICT_JSON)
vehicle_component_dict = load_json(VEHICLE_COMPONENT_DICT_JSON)
biomass_component_dict = load_json(BIOMASS_COMPONENT_DICT_JSON)

tech_component_dict = {
    "solar": solar_component_dict,
    "wind": wind_component_dict,
    "battery": battery_component_dict,
    "geothermal": geothermal_component_dict,
    "hydroelectric": hydroelectric_component_dict,
    "hydrogen": hydrogen_component_dict,
    "nuclear": nuclear_component_dict,
    "vehicle": vehicle_component_dict,
    "biomass": biomass_component_dict
}

def get_component_dict_value(tech, component):
    """Retrieve the value from the tech_component_dict based on tech and component."""
    
    # Check if the tech is valid
    if tech in tech_component_dict:
        # Return the component value if it exists
        return tech_component_dict[tech].get(component, None)  # Returns None if component not found
    return None  # Returns None if tech not found

# Example usage
#print(get_component_dict_value("solar", "polysilicon"))  
# Should return the value for "polysilicon" in the solar component dictionary

def get_reversed_component_dicts():
    """Create reversed dictionaries where codes are keys and component names are values."""
    reversed_tech_component_dict = {}
    
    for tech, component_dict in tech_component_dict.items():
        # Reverse the key-value pairs for each technology
        reversed_tech_component_dict[tech] = {v: k for k, v in component_dict.items()}
    
    return reversed_tech_component_dict

# Create reversed dictionaries
reversed_component_dicts = get_reversed_component_dicts()

def get_component_text(tech, component_code):
    """
    Retrieve the component text based on technology and component code.
    
    Args:
        tech (str): Technology type (e.g., "battery", "solar", etc.)
        component_code (str): The component code (e.g., "00", "01", etc.)
    
    Returns:
        str: Component text if found, None otherwise
    """
    if tech in reversed_component_dicts:
        return reversed_component_dicts[tech].get(component_code, None)
    return None

# Example usage:
# print(get_component_text("battery", "00"))  # Should return "deployment"
# print(get_component_text("battery", "03"))  # Should return "cell_manufacturing"




