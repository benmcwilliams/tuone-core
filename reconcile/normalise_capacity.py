import sys; sys.path.append("..")
import pandas as pd
import re
from numerizer import numerize
from word2number import w2n
import math
import logging
from src.capacity_mappings import SCALE_MAP, TIME_MAP, METRIC_MAP, UNIT_NORMALIZATION, REGEX_PATTERNS
from src.config import FACTORY_TECH, FACTORY_TECH_CLEAN_CAPACITIES

# ========= Load Excel =========
def load_capacity_column(file_path):
    df = pd.read_excel(file_path)
    print(df.head())
    df["capacity"] = df["capacity"].fillna("")
    return df

# define overrides as a mapping of (product_lv1, product_lv2, metric) → multiplier
MULTIPLIER_OVERRIDE_MAP = {
    # For 1 tonne EAM = 1 kWh → GWh
    ("battery", "eam", "tonne"): 1 / 1e3,  # 1 kWh per kg → 1 MWh per tonne → 0.001 GWh

    # For EV/cars implied capacity
    ("battery", None, None): 50 / 1e6,     # 50 kWh per car → 0.00005 GWh

    # You can add more specific or fallback mappings here
}

KEYWORD_MULTIPLIER_MAP = {
    ("ev", "car", "vehicle", "electric vehicle", "electric car", "vehicle electric", "evs", "bevs", "phevs", "phev"): 50 / 1e6,
    ("van","vans"): 80 / 1e6,
    ("truck", "electric truck", "trucks", "fret truck", "fret trucks", "electric heavy-duty vehicles", "heavy-duty vehicles", "heavy-duty"): 300 / 1e6,
    ("bus", "electric bus", "buses", "electric buses"): 350 / 1e6,
}

# ========= Capacity Info Extraction =========
def extract_capacity_info(text):
    if not isinstance(text, str):
        return None, None, None
    text = text.strip()

    # Case: Range (e.g., 1,000–2,000 tonnes)
    match = re.match(REGEX_PATTERNS["range"], text, re.IGNORECASE)
    if match:
        logging.debug(f"Case range: {match}")
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
        logging.debug(f"Case approximate scale: {match}")
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
        logging.debug(f"Case approximate without scale: {match}")
        try:
            value = float(match.group(2).replace(",", ""))
            remaining = match.group(3).strip()
            return value, None, remaining
        except:
            pass

    # Case: Mixed fraction (e.g., "three and a half million")
    match = re.match(REGEX_PATTERNS["mixed_fraction_scaled"], text, re.IGNORECASE)
    if match:
        logging.debug(f"Mixed fraction: {match}")
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
        logging.debug(f"Case word with scale: {match}")
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
        logging.debug(f"Case numeric with scale: {match}")
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
        logging.debug(f"Case num with scale stuck: {match}")
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
        logging.debug(f"Numeric stuck to unit: {match}")
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
    """
    Extracts and normalizes a metric unit from the input text.

    Returns:
        - standardized metric string (e.g. 'tonne', 'gigawatt hour')
        - cleaned text with the metric removed
        - scale (e.g. 1e3 for kilotonne)
    """
    if not isinstance(text, str):
        return "", text, 1

    text_lower = text.lower()
    for pattern, mapped_unit in sorted(METRIC_MAP.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(pattern)}\b", text_lower):
            cleaned = re.sub(rf"\b{re.escape(pattern)}\b", "", text, flags=re.IGNORECASE).strip()

            # Normalize using UNIT_NORMALIZATION if available
            if mapped_unit in UNIT_NORMALIZATION:
                standard_metric, scale = UNIT_NORMALIZATION[mapped_unit]
                return standard_metric, cleaned, scale

            # Otherwise, return mapped unit with scale 1
            return mapped_unit, cleaned, 1

    # No match
    return "", text, 1


# ---------- GWh converter -------------------------------------------------
def normalize_to_gwh_and_flag(row, conversion=False, *,
                              multiplier_override: int | None = None):
    """
    Normalises any capacity number(s) to GWh.

    Parameters
    ----------
    row : Mapping-like (Pandas Series or dict)
    conversion : bool
        If True and multiplier_override is None  -> ×2 (Case 1 default)
    multiplier_override : {None, 2, 4}
        • None  -> use default behaviour (×2 when flag is True)  
        • 2 or 4 -> force that multiplier (lets capacity_logic choose Case 1 vs Case 2)

    Returns
    -------
    (capacity_normalised, flag_failed, metric_out, conversion)
    """
    value  = row.get("capacity_value")
    scale  = row.get("capacity_scale", 1)
    metric = row.get("capacity_metric")
    time   = row.get("capacity_time")

    # --------- basic validation ----------
    if value is None or metric is None:
        return None, True, None, conversion
    if pd.isna(scale):
        scale = 1
    if not isinstance(metric, str):
        return None, True, None, conversion

    metric = metric.strip().lower()
       # default 1-to-1 when unknown

    # --------- conversion helper ----------
    def _to_gwh(x):
        try:
            gwh_val = float(x) * scale 
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
        elif conversion:
            mult = 5*1e-6                                           # 5*1e-6

        return gwh_val * mult

    # --------- scalar vs iterable ----------
    if isinstance(value, (list, tuple)):
        converted = [_to_gwh(v) for v in value]
        if any(v is None or pd.isna(v) for v in converted):
            return None, True, None, conversion
        return converted, False, "gigawatt hour", conversion
    else:
        result = _to_gwh(value)
        if result is None or pd.isna(result):
            return None, True, None, conversion
        return result, False, "gigawatt hour", conversion

#no need
def normalize_to_vehicle_and_flag(row, conversion=False):
    """
    Converts vehicle counts → vehicle metric.
    If conversion=True, *2 is applied to the output.
    Returns: capacity_normalised, flag_failed, metric_out, conversion
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
            return None, True, None, conversion
        return converted, False, "vehicle", conversion
    else:
        result = _to_vehicle(value)
        if result is None or pd.isna(result):
            return None, True, None, conversion
        return result, False, "vehicle", conversion


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

def normalize_default(row): 
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
    if metric_lower in { "gigawatt"}:
        return converted, False, metric_lower, False
    else:
        return converted, False, metric_lower,False

# ========= Updated Capacity Logic =========
def capacity_logic(row):
    """
    Determines how to normalize capacity based on product type and metric.

    Priority:
    1. If capacity_metric contains 'gigawatt' → normalize_default (annualize, keep metric)
    2. If an explicit multiplier override exists for (product_lv1, product_lv2, metric) → use it
    3. VEHICLE rows with missing/placeholder metric → normalize to vehicles/year
    4. BATTERY special cases:
        4a. battery + eam + missing metric + EV keyword → keyword override (Case 2)
        4b. battery OR metric=='unit' + EV keyword → keyword override (Case 2)
        4c. battery + missing metric → fallback override (Case 1)
        4d. battery + metric present → to GWh (no extra conversion)
    5. Fallback → normalize_default
    Returns:
        value, flag_failed, metric_out, flag_conversion, normalization_case
    """
    product_lv1 = str(row.get("product_lv1", "")).strip().lower()
    product_lv2 = str(row.get("product_lv2", "")).strip().lower()
    capacity_text_raw = str(row.get("capacity_text", "") or "")
    capacity_text = capacity_text_raw.lower()

    metric_raw = row.get("capacity_metric")
    metric_str = str(metric_raw).strip().lower() if isinstance(metric_raw, str) else ""

    text = (
        capacity_text.replace(",", " ")
        .replace("-", " ")
        .replace("_", " ")
        .strip()
    )

    excludes = ["battery", "batteries", "cell", "cells", "pack", "packs",
                "module", "modules", "research and development"]

    # -------- TONNE or GIGAWATT always → GWh logic first
    if "gigawatt" in metric_str:
        return normalize_default(row)

    # -------- Check if a multiplier override applies
    key = (product_lv1, product_lv2 if product_lv2 else None, metric_str if metric_str else None)
    mult_override = MULTIPLIER_OVERRIDE_MAP.get(key)
    if mult_override is not None:
        return normalize_to_gwh_and_flag(row, conversion=False, multiplier_override=mult_override)

    # -------- VEHICLE rows
    if product_lv1 == "vehicle":
        if metric_is_missing(metric_raw) or metric_str == "unit":
            return normalize_to_vehicle_and_flag(row, conversion=False)

    # -------- BATTERY rows
    if product_lv1 == "battery" and product_lv2 == "eam" and metric_is_missing(metric_raw):
        if not any(exc in text for exc in excludes):
            logging.info(f"CASE 2 triggered: '{capacity_text}'")

            for keywords, override in KEYWORD_MULTIPLIER_MAP.items():
                if any(k in text for k in keywords):
                    return normalize_to_gwh_and_flag(row, conversion=True, multiplier_override=override)

    if product_lv1 == "battery" or metric_str == "unit": #could be or
        if not any(exc in text for exc in excludes):
            logging.info(f"CASE 2 triggered: '{capacity_text}'")

            for keywords, override in KEYWORD_MULTIPLIER_MAP.items():
                if any(k in text for k in keywords):
                    return normalize_to_gwh_and_flag(row, conversion=True, multiplier_override=override)

        if metric_is_missing(metric_raw):
            logging.info("CASE 1 triggered")
            fallback_override = MULTIPLIER_OVERRIDE_MAP.get(("battery", None, None))
            return normalize_to_gwh_and_flag(row, conversion=True, multiplier_override=fallback_override)

        return normalize_to_gwh_and_flag(row, conversion=False)


    # -------- Fallback
    return normalize_default(row)


# ========= Pipeline Execution =========
def run_capacity_normalisation_pipeline(file_path=FACTORY_TECH):
    # EDITED - reading a df not file_path
    df = load_capacity_column(file_path)

    # Extract value, scale (from numbers/words), and raw remainder text
    df[["capacity_value", "capacity_scale", "capacity_text"]] = df["capacity"].apply(
        lambda x: pd.Series(extract_capacity_info(x))
    )

    # Extract normalized metric and scale adjustment (e.g. kilotonne → tonne + 1e3 scale)
    df[["capacity_metric", "capacity_text", "metric_scale"]] = df["capacity_text"].apply(
        lambda x: pd.Series(extract_normalized_metric_unit(x))
    )

    # Merge the metric scale multiplicatively
    df["capacity_scale"] = df["capacity_scale"].fillna(1) * df["metric_scale"].fillna(1)
    df.drop(columns=["metric_scale"], inplace=True)

    # Extract time units (e.g. per year)
    df[["capacity_time", "capacity_text"]] = df["capacity_text"].apply(
        lambda x: pd.Series(extract_normalized_time_unit(x))
    )

    # Normalize to final metric (GWh, vehicles, tonnes...)
    df[["capacity_normalized", "flag_failed", "capacity_metric_normalized", "flag_conversion"]] = df.apply(
        lambda row: pd.Series(capacity_logic(row)), axis=1
    )

    df.to_excel(FACTORY_TECH_CLEAN_CAPACITIES)

    return df


# ========= Main Run Block =========
if __name__ == "__main__":
    file_path = 'storage/output/clean_output_ben.xlsx'
    df_result = run_capacity_normalisation_pipeline(file_path)
    output_path = 'storage/output/clean_output_capacity.xlsx'
    df_result.to_excel(output_path, index=False)
    logging.info(df_result.head(10))

