import json
import ast
import logging
import pandas as pd

def bbox_to_geojson(bbox_input):
    """Convert bbox dictionary to GeoJSON Polygon format"""
    if pd.isna(bbox_input):
        return None
    
    # Handle string representation of dictionary
    if isinstance(bbox_input, str):
        try:
            # First try JSON parsing (for valid JSON strings)
            bbox_dict = json.loads(bbox_input)
        except json.JSONDecodeError:
            try:
                # If JSON fails, try ast.literal_eval for Python dict strings
                bbox_dict = ast.literal_eval(bbox_input)
            except (ValueError, SyntaxError):
                logging.warning(f"Could not parse bbox string: {bbox_input}")
                return None
    elif isinstance(bbox_input, dict):
        bbox_dict = bbox_input
    else:
        logging.warning(f"Unexpected bbox type: {type(bbox_input)}, value: {bbox_input}")
        return None
    
    # Validate required keys
    required_keys = ["west", "east", "north", "south"]
    if not all(key in bbox_dict for key in required_keys):
        logging.warning(f"bbox missing required keys. Available: {list(bbox_dict.keys())}")
        return None
    
    return {
        "type": "Polygon",
        "coordinates": [[
            [bbox_dict["west"], bbox_dict["south"]],
            [bbox_dict["east"], bbox_dict["south"]],
            [bbox_dict["east"], bbox_dict["north"]],
            [bbox_dict["west"], bbox_dict["north"]],
            [bbox_dict["west"], bbox_dict["south"]]
        ]]
    }