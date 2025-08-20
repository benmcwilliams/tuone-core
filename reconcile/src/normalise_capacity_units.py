import re
import logging

# ========= Unit Normalisation =========
UNIT_NORMALIZATION = {
    "watt hour":        ("gigawatt hour", 1e-9),
    "kilowatt hour":    ("gigawatt hour", 1e-6),
    "megawatt hour":    ("gigawatt hour", 1e-3),
    "gigawatt hour":    ("gigawatt hour", 1),
    "terawatt hour":    ("gigawatt hour", 1e3),

    "watt":        ("gigawatt", 1e-9),
    "kilowatt":    ("gigawatt", 1e-6),
    "megawatt":    ("gigawatt", 1e-3),
    "gigawatt":    ("gigawatt", 1),
    "terawatt":    ("gigawatt", 1e3),

    "tonne":            ("tonne", 1),
    "kilotonne":        ("tonne", 1e3),
    "megatonne":        ("tonne", 1e6),
}

# ========= Metric Mapping =========
METRIC_MAP = {
    "gw": "gigawatt", 
    "gigawatt": "gigawatt",
    "gigawatts": "gigawatt",
    "gwh": "gigawatt hour", 
    "gigawatt-hours": "gigawatt hour", 
    "giga watt hour": "gigawatt hour", 
    "giga watt hour": "gigawatt hour", 
    "giga-watt-hours": "gigawatt hour",
    "gigawatts hours": "gigawatt hour", 
    "giga watt hours":"gigawatt hour", 
    "gigawatt-hours":"gigawatt hour",
    "gigawatts-hour":"gigawatt hour",
    "gigawatt hours": "gigawatt hour",
    "mwh": "megawatt hour", 
    "megawatt-hours":"megawatt hour", 
    "megawatt-hour":"megawatt hour",
    "kwh": "kilowatt hour", 
    "twh": "terawatt hour", 
    "wh": "watt hour",
    "mw": "megawatt", 
    "mwp": "megawatt",
    "mwac": "megawatt",
    "megawatts direct current": "megawatt",
    "megawatts": "megawatt",
    "mwdc": "megawatt",
    "kw": "kilowatt", 
    "tw": "terawatt",
    "t": "tonne","tonne": 
    "tonne", "tonnes": 
    "tonne", "tons": 
    "tonne", "ton": "tonne", 
    "mt": "megatonne",
    "kt": "kilotonne", 
    "kilotonne": "kilotonne",
    "kg": "kilogram", 
    "g": "gram", 
    "units": "unit", 
    "unit": "unit",
    "battery modules": "battery modules",
    "modules": "battery modules",
    "batteries": "batteries",
    "battery systems": "battery systems",
    "hybrid battery systems": "battery systems",
    "battery packs": "battery packs",
    "packs": "battery packs"
}

# ========= Metric Unit Extraction =========
def normalise_capacity_unit(text):
    """
    Extracts and normalizes a metric unit from the input text using METRIC_MAP patterns.
    
    Searches for metric expressions like 'GWh', 'tonnes', 'MW' and converts them to 
    standardized metric names while providing scaling factors for unit conversions.
    
    Args:
        text: Input string that may contain metric unit expressions
        
    Returns:
        tuple: (standardized_metric, cleaned_text, scale)
            - standardized_metric: Standardized metric name (e.g., 'gigawatt hour', 'tonne')
                                   or empty string if no metric found
            - cleaned_text: Original text with the metric expression removed, or original text if no match
            - scale: Scaling factor for unit conversion (e.g., 1e-3 for MWh→GWh, 1e3 for kt→tonnes)
                     or 1 if no conversion needed
            
    Examples:
        >>> extract_normalized_metric_unit("50 GWh capacity")
        ('gigawatt hour', '50 capacity', 1)
        >>> extract_normalized_metric_unit("100 MWh production")
        ('gigawatt hour', '100 production', 0.001)
        >>> extract_normalized_metric_unit("200 kt of material")
        ('tonne', '200 of material', 1000)
        >>> extract_normalized_metric_unit("no metric here")
        ('', 'no metric here', 1)
    """
    if not isinstance(text, str):
        return "", text, 1

    text_lower = text.lower()
    logging.debug(f"Processing remainder text: {text_lower}")
    for pattern, mapped_unit in sorted(METRIC_MAP.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(pattern)}\b", text_lower):
            cleaned = re.sub(rf"\b{re.escape(pattern)}\b", "", text, flags=re.IGNORECASE).strip()
            logging.debug(f"Writing back cleaned text: {cleaned}")

            # Normalize using UNIT_NORMALIZATION if available
            if mapped_unit in UNIT_NORMALIZATION:
                logging.debug(f"{mapped_unit} is present in Unit Normalisation")
                standard_metric, scale = UNIT_NORMALIZATION[mapped_unit]
                return standard_metric, cleaned, scale

            # Otherwise, return mapped unit with scale 1
            logging.debug(f"{mapped_unit} is not present in Unit Normalisation, returning scale ==1.")
            return mapped_unit, cleaned, 1

    # No match
    logging.debug("No Match Found, returning empty.")
    return "", text, 1