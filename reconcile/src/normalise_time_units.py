import re
import logging

# ========= Time Mapping =========
TIME_MAP = {
    "yearly": "per year", "/year": "per year","/yr": "per year", "annually": "per year", "per annum": "per year", "1 year": "per year",
    "per year": "per year", "a year": "per year",
    "monthly": "per month", "per month": "per month", "/month": "per month", "a month": "per month",
    "weekly": "per week", "per week": "per week", "/week": "per week",
    "daily": "per day", "per day": "per day", "/day": "per day", "a day": "per day",
    "hourly": "per hour", "per hour": "per hour", "/hour": "per hour", "an hour": "per hour", "-hours": "per hour",  "-hour": "per hour", "- hour": "per hour", "hour":"per hour", "- hours": "per hour", " -hour": "per hour"
}

# ========= Time Unit Extraction =========
def extract_normalized_time_unit(text):

    """
    Extracts and normalizes time units from text using TIME_MAP patterns.
    
    Searches for time expressions like 'yearly', '/month', 'per day' and converts
    them to standardized formats while removing them from the original text.
    
    Args:
        text: Input string that may contain time unit expressions
        
    Returns:
        tuple: (normalized_time_unit, cleaned_text)
            - normalized_time_unit: Standardized time expression (e.g., 'per year', 'per month')
                                   or None if no time unit found
            - cleaned_text: Original text with the time expression removed, or original text if no match
            
    Examples:
        >>> extract_normalized_time_unit("50 GWh yearly production")
        ('per year', '50 GWh production')
        >>> extract_normalized_time_unit("100 MW /month capacity") 
        ('per month', '100 MW capacity')
        >>> extract_normalized_time_unit("no time unit here")
        (None, 'no time unit here')
    """

    if not isinstance(text, str):
        return None, text

    text_lower = text.lower()
    logging.debug(f"⏲️ Proccesing time text: {text_lower}")

    for pattern, replacement in TIME_MAP.items():
        if re.search(rf"(?<![a-zA-Z0-9]){re.escape(pattern)}(?![a-zA-Z0-9])|[-/]{re.escape(pattern)}", text_lower):
            cleaned = re.sub(rf"(?<![a-zA-Z0-9]){re.escape(pattern)}(?![a-zA-Z0-9])|[-/]{re.escape(pattern)}", "", text, flags=re.IGNORECASE).strip()
            logging.debug(f"👍 Found match: {replacement}")
            logging.debug(f"- - {cleaned} - - written back as remainder.")
            return replacement, cleaned
    return None, text
