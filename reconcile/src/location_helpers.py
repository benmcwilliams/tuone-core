import re

def clean_city(city_raw):
    if city_raw is None:
        return ""
    city = str(city_raw).strip().lower()
    if city in {"", "null", "none", "nan", "unknown", "tbd"}:
        return ""
    # Replace forward/backslashes with space and collapse multiple spaces
    city = re.sub(r"[\/\\]", " ", city)
    city = re.sub(r"\s+", " ", city).strip()
    return city

def clean_country(country_raw):
    if country_raw is None:
        return ""
    country = str(country_raw).strip().lower()
    if country in {"", "null", "none", "nan", "unknown", "tbd"}:
        return ""
    # Replace forward slashes, backslashes, periods, and multiple spaces
    country = re.sub(r"[\/\\\.]", " ", country)
    country = re.sub(r"\s+", " ", country).strip()
    return country

def normalize_city_key(city: str) -> str:
    """
    Normalize city name for use as MongoDB key:
    - lowercase
    - replace spaces and dots with underscores
    - collapse multiple underscores
    - remove non-alphanumeric characters (except underscore)
    """
    city = city.strip().lower()
    city = re.sub(r"[ .]", "_", city)         # replace space and dot with underscore
    city = re.sub(r"[^\w]", "", city)         # remove remaining invalid characters
    city = re.sub(r"__+", "_", city)          # collapse double/triple underscores
    return city.strip("_")                    # remove leading/trailing underscores
