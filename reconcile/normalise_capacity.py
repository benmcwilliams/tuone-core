import sys; sys.path.append("..")
import pandas as pd
import re
from numerizer import numerize
from word2number import w2n
import math


# ========= Load Excel =========
def load_capacity_column(file_path):
    df = pd.read_excel(file_path)
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
    "gw": "gigawatt", "gigawatt": "gigawatt",
    "gwh": "gigawatt hour", "gigawatt-hours": "gigawatt hour", "giga watt hour": "gigawatt hour", "giga watt hour": "gigawatt hour", "giga-watt-hours": "gigawatt hour",
    "gigawatts hours":"gigawatt hour", "giga watt hours":"gigawatt hour", "gigawatt-hours":"gigawatt hour","gigawatts-hour":"gigawatt hour","gigawatt hours": "gigawatt hour",
    "mwh": "megawatt hour", "kwh": "kilowatt hour", "twh": "terawatt hour", "wh": "watt hour",
    "mw": "megawatt", "kw": "kilowatt", "tw": "terawatt",
    "t": "tonne","tonne": "tonne", "tonnes": "tonne", "tons": "tonne", "ton": "tonne", 
    "mt": "megatonne",
    "kt": "kilotonne",
    "kg": "kilogram", 
    "g": "gram", 
    "units": "unit", "unit": "unit"
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

#========== Metric conversion ===============

UNIT_TO_GWH = {
    "watt hour": 1e-9,
    "kilowatt hour": 1e-6,
    "megawatt hour": 1e-3,
    "gigawatt hour": 1,
    "terawatt hour": 1e3
}



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
    match = re.match(REGEX_PATTERNS["num_with_scale_stuck"], text, re.IGNORECASE)
    if match:
        try:
            num_str, suffix, remaining = match.groups()
            value = float(num_str.replace(",", ""))
            if scale:
                return value, None, remaining.strip()
        except Exception:
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
        match = re.match(REGEX_PATTERNS["fallback"], numerized, re.IGNORECASE)
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


# ---------- GWh converter -------------------------------------------------
def normalize_to_gwh_and_flag(row, vehicle_to_gwh_or_battery_to_gwh=False, *,
                              multiplier_override: int | None = None):
    """
    Normalises any capacity number(s) to GWh.

    Parameters
    ----------
    row : Mapping-like (Pandas Series or dict)
    vehicle_to_gwh_or_battery_to_gwh : bool
        If True and multiplier_override is None  -> ×2 (Case 1 default)
    multiplier_override : {None, 2, 4}
        • None  -> use default behaviour (×2 when flag is True)  
        • 2 or 4 -> force that multiplier (lets capacity_logic choose Case 1 vs Case 2)

    Returns
    -------
    (capacity_normalised, flag_failed, metric_out, vehicle_to_gwh_or_battery_to_gwh)
    """
    value  = row.get("capacity_value")
    scale  = row.get("capacity_scale", 1)
    metric = row.get("capacity_metric")
    time   = row.get("capacity_time")

    # --------- basic validation ----------
    if value is None or metric is None:
        return None, True, None, vehicle_to_gwh_or_battery_to_gwh
    if pd.isna(scale):
        scale = 1
    if not isinstance(metric, str):
        return None, True, None, vehicle_to_gwh_or_battery_to_gwh

    metric = metric.strip().lower()
    gwh_factor = UNIT_TO_GWH.get(metric, 1)          # default 1-to-1 when unknown

    # --------- conversion helper ----------
    def _to_gwh(x):
        try:
            gwh_val = float(x) * scale * gwh_factor
        except Exception:
            return None

        # rate → annual energy
        if isinstance(time, str):
            t = time.strip().lower()
            gwh_val *= {"per day": 365, "per week": 52, "per month": 12}.get(t, 1)

        # decide multiplier
        mult = 1
        if multiplier_override is not None:
            mult = multiplier_override                         # 5*1e-6
        elif vehicle_to_gwh_or_battery_to_gwh:
            mult = 5*1e-6                                           # 5*1e-6

        return gwh_val * mult

    # --------- scalar vs iterable ----------
    if isinstance(value, (list, tuple)):
        converted = [_to_gwh(v) for v in value]
        if any(v is None or pd.isna(v) for v in converted):
            return None, True, None, vehicle_to_gwh_or_battery_to_gwh
        return converted, False, "gigawatt hour", vehicle_to_gwh_or_battery_to_gwh
    else:
        result = _to_gwh(value)
        if result is None or pd.isna(result):
            return None, True, None, vehicle_to_gwh_or_battery_to_gwh
        return result, False, "gigawatt hour", vehicle_to_gwh_or_battery_to_gwh


def normalize_to_vehicle_and_flag(row, vehicle_to_gwh_or_battery_to_gwh=False):
    """
    Converts vehicle counts → vehicle metric.
    If vehicle_to_gwh_or_battery_to_gwh=True, *2 is applied to the output.
    Returns: capacity_normalised, flag_failed, metric_out, vehicle_to_gwh_or_battery_to_gwh
    """
    value  = row.get("capacity_value")
    scale  = row.get("capacity_scale", 1)
    metric = row.get("capacity_metric")
    time   = row.get("capacity_time")

    if value is None or metric is None:
        return None, True, None, False
    if pd.isna(scale):
        scale = 1
    if not isinstance(metric, str):
        return None, True, None, False

    def _to_vehicle(x):
        try:
            v = float(x) * scale
        except Exception:
            return None

        if time == "per day":
            v *= 365
        elif time == "per week":
            v *= 52
        elif time == "per month":
            v *= 12
        elif time == "per year" or time is None:
            pass
        else:
            return None

        return v 

    if isinstance(value, (list, tuple)):
        converted = [_to_vehicle(v) for v in value]
        if not converted or any(v is None or pd.isna(v) for v in converted):
            return None, True, None, vehicle_to_gwh_or_battery_to_gwh
        return converted, False, "vehicle", vehicle_to_gwh_or_battery_to_gwh
    else:
        result = _to_vehicle(value)
        if result is None or pd.isna(result):
            return None, True, None, vehicle_to_gwh_or_battery_to_gwh
        return result, False, "vehicle", vehicle_to_gwh_or_battery_to_gwh


def metric_is_missing(metric):
    """
    Returns True when metric is:
      • None
      • NaN / pd.NA / math.nan
      • empty string
      • the string 'nan', 'none', or 'unit' (case-insensitive)
    """
    if metric is None:
        return True
    # NaN detection (works for float('nan'), pd.NA, numpy.nan, etc.)
    if isinstance(metric, float) and math.isnan(metric):
        return True
    if isinstance(metric, (pd._libs.missing.NAType, pd.api.extensions.ExtensionScalarOpsMixin)) and pd.isna(metric):
        return True
    if str(metric).strip().lower() in {"", "nan", "none", "unit"}:
        return True
    return False

def normalize_to_tonnes_or_gw(row): 
    """
    Converts 'tonne' or 'gigawatt' capacity value to yearly equivalent if time-based.
    Returns: capacity_normalised, flag_failed, capacity_metric_normalized
    """
    value  = row.get("capacity_value")
    scale  = row.get("capacity_scale", 1)
    metric = row.get("capacity_metric")
    time   = row.get("capacity_time")

    if value is None or metric is None:
        return None, True, None
    if pd.isna(scale):
        scale = 1
    if not isinstance(metric, str):
        return None, True, None

    def _to_annual_scaled(x):
        try:
            v = float(x) * scale
        except Exception:
            return None

        if time == "per day":
            v *= 365
        elif time == "per week":
            v *= 52
        elif time == "per month":
            v *= 12
        elif time == "per year" or time is None:
            pass
        else:
            return None

        return v

    if isinstance(value, (list, tuple)):
        converted = [_to_annual_scaled(v) for v in value]
        if not converted or any(v is None or pd.isna(v) for v in converted):
            return None, True, None
    else:
        converted = _to_annual_scaled(value)
        if converted is None or pd.isna(converted):
            return None, True, None

    metric_lower = metric.strip().lower()
    if metric_lower in {"tonne", "gigawatt"}:
        return converted, False, metric_lower
    else:
        return converted, False, metric_lower

def capacity_logic(row):
    """
    Determines how to normalize capacity based on product type and metric.

    Priority:
    1. If capacity_metric is tonne or gigawatt → normalize as GWh (via scale × time)
    2. If product = battery and capacity_text includes EV/cars but not battery/etc → Case 2
    3. If product = battery and metric is missing → Case 1
    4. If product = vehicle and metric is missing → convert to vehicle count
    5. Default: use normalize_to_gwh_and_flag
    """
    product_lv1 = str(row.get("product_lv1", "")).strip().lower()
    capacity_text = str(row.get("capacity_text", "")).lower()
    metric_raw = row.get("capacity_metric")
    metric_str = str(metric_raw).strip().lower() if isinstance(metric_raw, str) else ""

    text = (
        capacity_text.replace(",", " ")
        .replace("-", " ")
        .replace("_", " ")
        .strip()
    )

    includes = ["ev", "evs", "car", "cars", "vehicle", "vehicles"]
    excludes = ["battery", "batteries", "cell", "cells", "pack", "packs",
                "module", "modules", "research and development"]

    # -------- TONNE or GIGAWATT always → GWh logic first
    if "tonne" in metric_str or "gigawatt" in metric_str:
        return normalize_to_tonnes_or_gw(row)

    # -------- VEHICLE rows
    if product_lv1 == "vehicle":
        if metric_is_missing(metric_raw) or metric_str == "unit":
            return normalize_to_vehicle_and_flag(row, vehicle_to_gwh_or_battery_to_gwh=False)

    # -------- BATTERY rows
    if product_lv1 == "battery" or metric_str == "unit":
        if any(inc in text for inc in includes) and not any(exc in text for exc in excludes):
            print(f"CASE 2 triggered: '{capacity_text}'")
            return normalize_to_gwh_and_flag(row, vehicle_to_gwh_or_battery_to_gwh=True, multiplier_override=50/1e6)

        if metric_is_missing(metric_raw):
            print("CASE 1 triggered")
            return normalize_to_gwh_and_flag(row, vehicle_to_gwh_or_battery_to_gwh=True, multiplier_override=50/1e6)

        return normalize_to_gwh_and_flag(row, vehicle_to_gwh_or_battery_to_gwh=False)

    # -------- Fallback
    return normalize_to_gwh_and_flag(row, vehicle_to_gwh_or_battery_to_gwh=False)




# ========= Pipeline Execution =========
def run_extraction_pipeline(file_path):
    df = load_capacity_column(file_path)
    df[["capacity_value", "capacity_scale", "capacity_text"]] = df["capacity"].apply(lambda x: pd.Series(extract_capacity_info(x)))
    df[["capacity_metric", "capacity_text"]] = df["capacity_text"].apply(lambda x: pd.Series(extract_normalized_metric_unit(x)))
    df[["capacity_time", "capacity_text"]] = df["capacity_text"].apply(lambda x: pd.Series(extract_normalized_time_unit(x)))
    
    # df[["capacity_normalized", "flag_failed", "capacity_metric_normalized"]] = df.apply(lambda row: pd.Series(normalize_to_gwh_and_flag(row)), axis=1)
    df[
        ["capacity_normalized",
        "flag_failed",
        "capacity_metric_normalized",
        "vehicle_to_gwh_or_battery_to_gwh"]
    ] = df.apply(lambda row: pd.Series(capacity_logic(row)), axis=1)
    return df


# ========= Main Run Block =========
if __name__ == "__main__":
    file_path = 'storage/output/clean_output_ben.xlsx'
    df_result = run_extraction_pipeline(file_path)
    output_path = 'storage/output/clean_output_capacity.xlsx'
    df_result.to_excel(output_path, index=False)
    print(df_result.head(10))

