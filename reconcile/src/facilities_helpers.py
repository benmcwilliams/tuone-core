def bbox_to_geojson(bbox_dict):
    """Convert bbox dictionary to GeoJSON Polygon format"""
    if not bbox_dict or not isinstance(bbox_dict, dict):
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