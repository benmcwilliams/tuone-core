import json
from pymongo import MongoClient
import requests
import time
from typing import Tuple, Optional

# Connect to MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["clean_tech_db"]
article_entities_collection = db["article_entities"]

def load_company_mappings():
    """Load company name variations from JSON file"""
    with open('src/mappings/company_name_variations.json', 'r') as f:
        return json.load(f)

def find_master_company(company_name, company_mappings):
    """
    Find the master company name for a given company name variation.
    Always returns a value, even if no mapping exists.
    """
    for master_company, variations in company_mappings.items():
        if company_name in variations or company_name == master_company:
            return master_company
    return company_name  # Ensure it always returns something

def get_lat_lon(location: dict) -> Tuple[Optional[float], Optional[float]]:
    """
    Get latitude and longitude for a location using OpenStreetMap's Nominatim API.
    
    Args:
        location (dict): Dictionary containing city and country fields
        
    Returns:
        tuple: (latitude, longitude) as floats, or (None, None) if location not found
    """
    # Skip if no location provided
    if not location or not isinstance(location, dict):
        return None, None
    
    city = location.get('city')
    country = location.get('country')
    
    # Skip city if it's "null"
    if city == "null":
        city = None
    
    # Skip if no valid location info
    if not country and not city:
        return None, None
        
    # Construct query string using only valid components
    if city and country:
        query = f"{city}, {country}"
    elif country:
        query = country
    elif city:
        query = city
    else:
        return None, None
    
    # Nominatim API endpoint
    url = "https://nominatim.openstreetmap.org/search"
    
    # Request parameters
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "addressdetails": 1  # Get additional details for debugging
    }
    
    # Update User-Agent with valid contact info
    headers = {
        "User-Agent": "CleanTechDB/1.0",  # Simplified user agent
        "Accept-Language": "en"  # Request English results
    }
    
    try:
        # Respect rate limits
        time.sleep(1.1)
        
        response = requests.get(url, params=params, headers=headers)
        
        # Check status code before parsing JSON
        response.raise_for_status()
        
        results = response.json()
        
        if not results:
            print(f"No results found for query: {query}")
            
            # Try alternative query format for countries
            if country and not city:
                alternative_params = params.copy()
                alternative_params["country"] = country
                print(f"Trying alternative query with country parameter:")
                print(f"Params: {alternative_params}")
                
                time.sleep(1.1)  # Respect rate limits
                alternative_response = requests.get(url, params=alternative_params, headers=headers)
                alternative_results = alternative_response.json()
                print(f"Alternative Response: {json.dumps(alternative_results, indent=2)}")
                
                if alternative_results:
                    results = alternative_results
        
        if results and len(results) > 0:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            print(f"Found coordinates: {lat}, {lon}")
            return lat, lon
            
        return None, None
        
    except requests.exceptions.RequestException as e:
        print(f"Error geocoding location '{query}': {str(e)}")
        print(f"Full error: {e.__class__.__name__}: {str(e)}")
        return None, None
    except (ValueError, KeyError) as e:
        print(f"Error parsing geocoding response for '{query}': {str(e)}")
        print(f"Full error: {e.__class__.__name__}: {str(e)}")
        return None, None

def process_entities():
    """
    Fetches extracted nodes from MongoDB, adds company_master field,
    and attaches lat/lon to locations. Updates the entries in MongoDB.
    """
    company_mappings = load_company_mappings()  # Load mappings once
    
    articles = article_entities_collection.find({})
    
    for article in articles:
        article_id = article["article_id"]
        nodes = article.get("nodes", [])

        for i, node in enumerate(nodes):
            update_fields = {}

            if "name" in node and isinstance(node["name"], str):
                master_name = find_master_company(node["name"], company_mappings)
                update_fields[f"nodes.{i}.company_master"] = master_name  # Always set

            if "location" in node:
                lat, lon = get_lat_lon(node["location"])
                if lat is not None and lon is not None:
                    update_fields[f"nodes.{i}.latitude"] = lat
                    update_fields[f"nodes.{i}.longitude"] = lon

            # Apply updates only if there are changes
            if update_fields:
                article_entities_collection.update_one(
                    {"article_id": article_id},
                    {"$set": update_fields}
                )

        print(f"✅ Processed Article ID: {article_id}")

    print("✅ Entity processing complete!")

if __name__ == "__main__":
    process_entities()