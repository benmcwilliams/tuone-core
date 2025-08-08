# ========= Scale Mapping =========
SCALE_MAP = {
    # Thousand
    "thousand": 1e3, "thousands": 1e3,
    "k": 1e3, "K": 1e3,
    "kilo": 1e3, "kilos": 1e3,
    
    # Million
    "million": 1e6, "millions": 1e6,
    "m": 1e6, "M": 1e6,
    "mn": 1e6, "MN": 1e6,
    "mln": 1e6, "MLN": 1e6,
    
    # Billion
    "billion": 1e9, "billions": 1e9,
    "b": 1e9, "B": 1e9,
    "bn": 1e9, "BN": 1e9,
    "bln": 1e9, "BLN": 1e9,
    
    # Trillion
    "trillion": 1e12, "trillions": 1e12,
    "t": 1e12, "T": 1e12,
    "tn": 1e12, "TN": 1e12,
    "trn": 1e12, "TRN": 1e12
}

# ========= Time Mapping =========
TIME_MAP = {
    "yearly": "per year", "/year": "per year","/yr": "per year", "annually": "per year", "per annum": "per year", "1 year": "per year",
    "per year": "per year", "a year": "per year",
    "monthly": "per month", "per month": "per month", "/month": "per month", "a month": "per month",
    "weekly": "per week", "per week": "per week", "/week": "per week",
    "daily": "per day", "per day": "per day", "/day": "per day", "a day": "per day",
    "hourly": "per hour", "per hour": "per hour", "/hour": "per hour", "an hour": "per hour", "-hours": "per hour",  "-hour": "per hour", "- hour": "per hour", "hour":"per hour", "- hours": "per hour", " -hour": "per hour"
}

# ========= Metric Mapping =========
METRIC_MAP = {
    "gw": "gigawatt", "gigawatt": "gigawatt",
    "gwh": "gigawatt hour", "gigawatt-hours": "gigawatt hour", "giga watt hour": "gigawatt hour", "giga watt hour": "gigawatt hour", "giga-watt-hours": "gigawatt hour",
    "gigawatts hours":"gigawatt hour", "giga watt hours":"gigawatt hour", "gigawatt-hours":"gigawatt hour","gigawatts-hour":"gigawatt hour","gigawatt hours": "gigawatt hour",
    "mwh": "megawatt hour", "megawatt-hours":"megawatt hour", "megawatt-hour":"megawatt hour",
    "kwh": "kilowatt hour", "twh": "terawatt hour", "wh": "watt hour",
    "mw": "megawatt", "kw": "kilowatt", "tw": "terawatt",
    "t": "tonne","tonne": "tonne", "tonnes": "tonne", "tons": "tonne", "ton": "tonne", 
    "mt": "megatonne",
    "kt": "kilotonne", "kilotonne": "kilotonne",
    "kg": "kilogram", 
    "g": "gram", 
    "units": "unit", "unit": "unit"
}

UNIT_NORMALIZATION = {
    "watt hour":        ("gigawatt hour", 1e-9),
    "kilowatt hour":    ("gigawatt hour", 1e-6),
    "megawatt hour":    ("gigawatt hour", 1e-3),
    "gigawatt hour":    ("gigawatt hour", 1),
    "terawatt hour":    ("gigawatt hour", 1e3),

    "tonne":            ("tonne", 1),
    "kilotonne":        ("tonne", 1e3),
    "megatonne":        ("tonne", 1e6),
}

# ========= Regex Patterns =========
REGEX_PATTERNS = {
    "range": r"^([0-9,.]+)\s*(?:to|-|–|—)\s*([0-9,.]+)\s+(.*)",
    
    "approx_scaled": r"^(almost|nearly|around|about|approximately|approx\.?|over|under|more than|less than)\s+([0-9,.]+)\s+(thousand|million|billion|trillion)\b\s*(.*)",
    
    "approx": r"^(almost|nearly|around|about|approximately|approx\.?|over|under|more than|less than|up to)\s+([0-9,.]+)\s+(.*)",
    
    "fractional_half": r"^(half|a half|one half|one and a half| half a)\s+(thousand|million|billion|trillion)\b\s*(.*)",
    
    "compound_word_scale": r"^([a-z\s-]+)\s+(thousand|million|billion|trillion)\b\s*(.*)",
    
    "num_with_scale": r"^([0-9,.]+)\s+(thousand|million|billion|trillion)\b\s*(.*)",
    
    "word_with_scale": r"^([a-z\s-]+)\s+(thousand|million|billion|trillion)\b\s*(.*)",
    
    "num_with_scale_stuck": r"^([0-9.,]+)\s*([a-zA-Z]+)\b\s*(.*)",
    
    "plain_numeric": r"^([0-9,.]+)\s*([a-zA-Z/]+.*)",

    "mixed_fraction_scaled": r"^([a-z0-9\s-]+?)\s+and a half\s+(thousand|million|billion|trillion)\b\s*(.*)",
    
    "fallback" : r"^([0-9,.]+)\s*(thousand|million|billion|trillion)?\b\s*(.*)" 

}