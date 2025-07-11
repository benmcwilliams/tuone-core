import pandas as pd
import re
from numerizer import numerize
from word2number import w2n


# ========= Load Excel =========
def load_capacity_column(file_path):
    df = pd.read_excel(file_path)
    df = df[["capacity", "product"]].copy()
    df["capacity"] = df["capacity"].fillna("")
    return df

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
    "gw": "gigawatt",
    "gwh": "gigawatt hour", "giga watt hour": "gigawatt hour", "giga watt hour": "gigawatt hour", "giga-watt-hours": "gigawatt hour",
    "gigawatts hours":"gigawatt hour","gigawatts-hours":"gigawatt hour", "gigawatt-hours":"gigawatt hour","gigawatts-hour":"gigawatt hour","gigawatt hours": "gigawatt hour",
    "mwh": "megawatt hour", "kwh": "kilowatt hour", "twh": "terawatt hour", "wh": "watt hour",
    "mw": "megawatt", "kw": "kilowatt", "tw": "terawatt",
    "t": "tonne","tonne": "tonne", "tonnes": "tonne", "tons": "tonne", "ton": "tonne", "mt": "megatonne", "kt": "kilotonne",
    "kg": "kilogram", "g": "gram", "units": "unit", "unit": "unit"
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
    
    "plain_numeric": r"^([0-9,.]+)\s*([a-zA-Z/]+.*)",

    "mixed_fraction_scaled": r"^([a-z0-9\s-]+?)\s+and a half\s+(thousand|million|billion|trillion)\b\s*(.*)"

}

#========== Metric conversion ===============
EV_CONVERSION = {
    "cell": 1,
    "module": 1,
    "pack": 1
} # 1 EV = x GWh of cells or module or packs

BUS_CONVERSION = {
    "cell": 1,
    "module": 1,
    "pack": 1
}

TRUCK_CONVERSION = {
    "cell": 1,
    "module": 1,
    "pack": 1
}

INTER_PRODUCT_CONVERSION = {
    "ev": EV_CONVERSION,
    "car": EV_CONVERSION,         # same as EV
    "vehicle": EV_CONVERSION,     # same as EV
    "bus": BUS_CONVERSION,
    "truck": TRUCK_CONVERSION
}

UNIT_TO_GWH = {
    "watt hour": 1e-9,
    "kilowatt hour": 1e-6,
    "megawatt hour": 1e-3,
    "gigawatt hour": 1,
    "terawatt hour": 1e3
}

# PRODUCT_UNIT_TO_GWH = {
#     "cell": 0.0000005,
#     "module": 0.0000005,
#     "battery": 0.0000005,
#     "pack": 0.0000005
# }


# ========= Capacity Info Extraction =========
def extract_capacity_info(text):
    if not isinstance(text, str):
        return None, None, None
    text = text.strip()

    # Case: Range (e.g., 1,000–2,000 tonnes)
    match = re.match(REGEX_PATTERNS["range"], text, re.IGNORECASE)
    if match:
        try:
            val1 = float(match.group(1).replace(",", ""))
            val2 = float(match.group(2).replace(",", ""))
            remaining = match.group(3).strip()
            return [val1, val2], None, remaining
        except:
            pass

    # Case: Approximate with scale (e.g., about 1 million)
    match = re.match(REGEX_PATTERNS["approx_scaled"], text, re.IGNORECASE)
    if match:
        try:
            value = float(match.group(2).replace(",", ""))
            scale = SCALE_MAP.get(match.group(3).lower())
            remaining = match.group(4).strip()
            return value, scale, remaining
        except:
            pass

    # Case: Approximate without scale (e.g., about 2000)
    match = re.match(REGEX_PATTERNS["approx"], text, re.IGNORECASE)
    if match:
        try:
            value = float(match.group(2).replace(",", ""))
            remaining = match.group(3).strip()
            return value, None, remaining
        except:
            pass

    # Case: Mixed fraction (e.g., "three and a half million")
    match = re.match(REGEX_PATTERNS["mixed_fraction_scaled"], text, re.IGNORECASE)
    if match:
        try:
            whole = match.group(1).strip()
            scale_str = match.group(3).lower()
            remaining = match.group(4).strip()
            scale = SCALE_MAP.get(scale_str)
            if scale:
                if whole.isdigit():
                    whole_val = float(whole)
                else:
                    whole_val = w2n.word_to_num(whole)
                return whole_val + 0.5, scale, remaining
        except:
            pass

    # Case: Word + scale (e.g., one million)
    match = re.match(REGEX_PATTERNS["word_with_scale"], text, re.IGNORECASE)
    if match:
        try:
            value = w2n.word_to_num(match.group(1).strip())
            scale = SCALE_MAP.get(match.group(2).lower())
            remaining = match.group(3).strip()
            return value, scale, remaining
        except:
            pass

    # Case: Numeric + scale (e.g., 2 million)
    match = re.match(REGEX_PATTERNS["num_with_scale"], text, re.IGNORECASE)
    if match:
        try:
            value = float(match.group(1).replace(",", ""))
            scale = SCALE_MAP.get(match.group(2).lower())
            remaining = match.group(3).strip()
            return value, scale, remaining
        except:
            pass

    # Case: Numeric + suffix (e.g., 5k, 12.3B)
    match = re.match(r"^([0-9.,]+)\s*([a-zA-Z]+)\b\s*(.*)", text)
    if match:
        try:
            num_str, suffix, remaining = match.groups()
            value = float(num_str.replace(",", ""))
            scale = SCALE_MAP.get(suffix)
            if scale:
                return value * scale, scale, remaining.strip()
        except:
            pass

    # Case: Numeric stuck to unit (e.g., 20GWh, 1000MW/year)
    match = re.match(REGEX_PATTERNS["plain_numeric"], text, re.IGNORECASE)
    if match:
        try:
            value = float(match.group(1).replace(",", ""))
            remaining = match.group(2).strip()
            return value, None, remaining
        except:
            pass

    # Fallback: Clean and parse with numerizer
    try:
        modifiers = ["up to", "about", "around", "approximately", "approx", "nearly", "almost", "more than", "less than", "over", "under"]
        text_lower = text.lower()
        for mod in modifiers:
            if text_lower.startswith(mod):
                text_lower = text_lower[len(mod):].strip()
                break

        numerized = numerize(text_lower)
        match = re.match(r"^([0-9,.]+)\s*(thousand|million|billion|trillion)?\b\s*(.*)", numerized, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(",", ""))
            scale_str = match.group(2)
            remaining = match.group(3).strip()
            scale = SCALE_MAP.get(scale_str.lower()) if scale_str else None
            return value, scale, remaining
    except:
        pass

    return None, None, text


# ========= Time Unit Extraction =========
def extract_normalized_time_unit(text):
    if not isinstance(text, str):
        return None, text

    text_lower = text.lower()
    for pattern, replacement in TIME_MAP.items():
        if re.search(rf"(?<![a-zA-Z0-9]){re.escape(pattern)}(?![a-zA-Z0-9])|[-/]{re.escape(pattern)}", text_lower):
            cleaned = re.sub(rf"(?<![a-zA-Z0-9]){re.escape(pattern)}(?![a-zA-Z0-9])|[-/]{re.escape(pattern)}", "", text, flags=re.IGNORECASE).strip()
            return replacement, cleaned
    return None, text


# ========= Metric Unit Extraction =========
def extract_normalized_metric_unit(text):
    if not isinstance(text, str):
        return "", text

    text_lower = text.lower()
    for pattern, replacement in METRIC_MAP.items():
        # match units stuck to numbers or attached with hyphen/slash
        if re.search(rf"(?<![a-zA-Z0-9]){re.escape(pattern)}(?![a-zA-Z0-9])|[-/]{re.escape(pattern)}", text_lower):
            cleaned = re.sub(rf"(?<![a-zA-Z0-9]){re.escape(pattern)}(?![a-zA-Z0-9])|[-/]{re.escape(pattern)}", "", text, flags=re.IGNORECASE).strip()
            return replacement, cleaned
    return "", text

# ======== Metric conversions =========
def compute_conversion_from_cols(product, text):
    product = product.lower() if isinstance(product, str) else ""
    text = text.lower() if isinstance(text, str) else ""

    # Skip all logic if text is empty
    if not text.strip():
        return None

    for final_product in INTER_PRODUCT_CONVERSION:
        if final_product in text:
            for intermediate in INTER_PRODUCT_CONVERSION[final_product]:
                if intermediate in product:
                    return INTER_PRODUCT_CONVERSION[final_product][intermediate]

    return None

def normalize_to_gwh_and_flag(row):
    value   = row.get("value")
    scale   = row.get("scale", 1)
    metric  = row.get("metric")
    time    = row.get("time")

    if value is None or metric is None:
        return None, True, False
    if pd.isna(scale):
        scale = 1
    if not isinstance(metric, str):
        return None, True, False

    metric = metric.strip().lower()
    gwh_factor = UNIT_TO_GWH.get(metric)
    if gwh_factor is None:
        return None, True, False

    def _to_gwh(x):
        try:
            gwh_val = float(x) * scale * gwh_factor
        except Exception:
            return None
        match time:
            case "per day":   gwh_val *= 365
            case "per week":  gwh_val *= 52
            case "per month": gwh_val *= 12
            case "per year" | None: pass
            case _: return None
        return gwh_val

    match value:
        case list() | tuple():
            converted = [_to_gwh(v) for v in value]
            if not converted or any(v is None or pd.isna(v) for v in converted):
                return None, True, False
            return converted, False, True
        case _:
            result = _to_gwh(value)
            if result is None or pd.isna(result):
                return None, True, False
            return result, False, True



# ========= Pipeline Execution =========
def run_extraction_pipeline(df):
    # df = load_capacity_column(file_path)
    df[["value", "scale", "text"]] = df["capacity"].apply(lambda x: pd.Series(extract_capacity_info(x)))
    df[["metric", "text"]] = df["text"].apply(lambda x: pd.Series(extract_normalized_metric_unit(x)))
    df[["time", "text"]] = df["text"].apply(lambda x: pd.Series(extract_normalized_time_unit(x)))
    
    # Add the conversion column
    df["conversion"] = df["product"].combine(df["text"], compute_conversion_from_cols)
    df[["value_gwh_normalized", "flag_failed", "gwh_normalized"]] = df.apply(lambda row: pd.Series(normalize_to_gwh_and_flag(row)), axis=1)
    return df


# ========= Main Run Block =========
if __name__ == "__main__":
    file_path = 'C:/Users/marie.juge/OneDrive - Bruegel/Desktop/tuone/tuone_v6/reconcile/storage/output/clean_output_ben.xlsx'
    df_result = run_extraction_pipeline(file_path)
    output_path = 'C:/Users/marie.juge/OneDrive - Bruegel/Desktop/tuone/tuone_v6/reconcile/storage/output/saved_result.xlsx'
    df_result.to_excel(output_path, index=False)
    df_text = df_result["text"].unique()
    print(df_result.head(10))


# "conversion"column built based 
# Case when product contains cell or battery or modules or pack and capacity metric contains vehicles or cars or buses or EV -> apply interproduct conversion disctionnary
# Else apply dictionnary for product to GWh 
