import pandas as pd
import re
from word2number import w2n

# ========= Load Excel =========
def load_capacity_column(file_path):
    df = pd.read_excel(file_path)
    df = df[["capacity"]].copy()
    df["capacity"] = df["capacity"].fillna("")
    return df

# ========= Scale Mapping =========
SCALE_MAP = {
    "thousand": 1e3,
    "million": 1e6,
    "billion": 1e9,
    "trillion": 1e12
}

# ========= Time Mapping =========
TIME_MAP = {
    "yearly": "per year", "/year": "per year", "annually": "per year", "per annum": "per year",
    "per year": "per year", "a year": "per year",
    "monthly": "per month", "per month": "per month", "/month": "per month", "a month": "per month",
    "weekly": "per week", "per week": "per week", "/week": "per week",
    "daily": "per day", "per day": "per day", "/day": "per day", "a day": "per day",
    "hourly": "per hour", "per hour": "per hour", "/hour": "per hour", "an hour": "per hour"
}

# ========= Metric Mapping =========
METRIC_MAP = {
    "gwh": "gigawatt hour", "mwh": "megawatt hour", "kwh": "kilowatt hour", "twh": "terawatt hour", "wh": "watt hour",
    "mw": "megawatt", "kw": "kilowatt", "tw": "terawatt",
    "tonne": "tonne", "tonnes": "tonne", "tons": "tonne", "mt": "megatonne", "kt": "kilotonne",
    "kg": "kilogram", "g": "gram"
}

# ========= Capacity Info Extraction =========
def extract_capacity_info(text):
    if not isinstance(text, str):
        return None, None, None
    text = text.strip()

    # Case 0: Range
    match_range = re.match(r"^([0-9,.]+)\s*(?:to|-|–|—)\s*([0-9,.]+)\s+(.*)", text, re.IGNORECASE)
    if match_range:
        try:
            val1 = float(match_range.group(1).replace(",", ""))
            val2 = float(match_range.group(2).replace(",", ""))
            remaining = match_range.group(3).strip()
            return [val1, val2], None, remaining
        except:
            pass

    # Case 1: Numeric with scale (e.g., 1.2 million EVs)
    match_num = re.match(r"^([0-9,.]+)\s+(thousand|million|billion|trillion)\b\s*(.*)", text, re.IGNORECASE)
    if match_num:
        value = float(match_num.group(1).replace(",", ""))
        scale = SCALE_MAP.get(match_num.group(2).lower())
        remaining = match_num.group(3).strip()
        return value, scale, remaining

    # Case 2: Word with scale (e.g., one million EVs)
    match_word = re.match(r"^([a-z\s-]+)\s+(thousand|million|billion|trillion)\b\s*(.*)", text, re.IGNORECASE)
    if match_word:
        try:
            value = w2n.word_to_num(match_word.group(1).strip())
            scale = SCALE_MAP.get(match_word.group(2).lower())
            remaining = match_word.group(3).strip()
            return value, scale, remaining
        except:
            pass

    # Case 3: Plain numeric (e.g., 5000 tonnes)
    match_plain = re.match(r"([0-9,.]+)\s+(.*)", text)
    if match_plain:
        return float(match_plain.group(1).replace(",", "")), None, match_plain.group(2).strip()

    return None, None, text

# ========= Time Unit Extraction =========
def extract_normalized_time_unit(text):
    if not isinstance(text, str):
        return None, text

    text_lower = text.lower()
    for pattern, replacement in TIME_MAP.items():
        if re.search(rf"\b{re.escape(pattern)}\b", text_lower):
            cleaned = re.sub(rf"\b{re.escape(pattern)}\b", "", text, flags=re.IGNORECASE).strip()
            return replacement, cleaned
    return None, text

# ========= Metric Unit Extraction =========
def extract_normalized_metric_unit(text):
    if not isinstance(text, str):
        return None, text

    text_lower = text.lower()
    for pattern, replacement in METRIC_MAP.items():
        if re.search(rf"\b{re.escape(pattern)}\b", text_lower):
            cleaned = re.sub(rf"\b{re.escape(pattern)}\b", "", text, flags=re.IGNORECASE).strip()
            return replacement, cleaned
    return None, text

# ========= Pipeline Execution =========
def run_extraction_pipeline(file_path):
    df = load_capacity_column(file_path)
    df[["value", "scale", "text"]] = df["capacity"].apply(lambda x: pd.Series(extract_capacity_info(x)))
    df[["time", "text"]] = df["text"].apply(lambda x: pd.Series(extract_normalized_time_unit(x)))
    df[["metric", "text"]] = df["text"].apply(lambda x: pd.Series(extract_normalized_metric_unit(x)))
    return df

# ========= Main Run Block =========
if __name__ == "__main__":
    file_path = 'storage/output/clean_output_ben.xlsx'
    df_result = run_extraction_pipeline(file_path)
    df_result.to_excel("test.xlsx")
    print(df_result.head(20))
