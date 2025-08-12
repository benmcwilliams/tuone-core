import sys; sys.path.append("..")
import json
from pathlib import Path
import pandas as pd
import re
from numerizer import numerize
from word2number import w2n
import math
import logging
from reconcile.src.capacity_constants import SCALE_MAP, TIME_MAP, METRIC_MAP, UNIT_NORMALIZATION, REGEX_PATTERNS, TARGET_UNIT_BY_TECH
from reconcile.src.capacity_helpers import load_capacity_column, apply_scale, annualize, multiply_vals, has_nan
from src.config import FACTORY_TECH, FACTORY_TECH_CLEAN_CAPACITIES

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

def get_explicit_override(product_lv1: str | None, product_lv2: str | None, metric_str: str | None):
    """
    Look up (lv1, lv2, metric) in MULTIPLIER_OVERRIDE_MAP.
    All inputs should already be lowercased or None.
    """
    key = (product_lv1 or None, product_lv2 or None, metric_str or None)
    return MULTIPLIER_OVERRIDE_MAP.get(key), key

def detect_keyword_multiplier(text_lower: str):
    """
    Scan KEYWORD_MULTIPLIER_MAP once and return the first match found.
    Returns (multiplier, matched_keyword, keywords_tuple) or (None, None, None).
    """
    for keywords, mult in KEYWORD_MULTIPLIER_MAP.items():
        for k in keywords:
            if k in text_lower:
                return mult, k, keywords
    return None, None, None

def load_capacity_rule_overrides(path="storage/config/capacity_rules.json"):
    p = Path(path)
    if not p.exists():
        logging.info("No external capacity_rules.json found at %s (skipping overrides).", path)
        return

    try:
        data = json.loads(p.read_text())
    except Exception as e:
        logging.warning("Failed to read %s: %s", path, e)
        return

    # 1) multiplier_overrides: list of [lv1, lv2, metric, multiplier]
    updated = 0
    for item in data.get("multiplier_overrides", []):
        if len(item) != 4:
            continue
        lv1, lv2, metric, mult = item
        MULTIPLIER_OVERRIDE_MAP[(lv1, lv2, metric)] = mult
        updated += 1
    if updated:
        logging.info("Applied %d multiplier_overrides from %s.", updated, path)

    # 2) keyword_overrides: list of [[kw1, kw2, ...], multiplier]
    updated = 0
    for item in data.get("keyword_overrides", []):
        if len(item) != 2:
            continue
        keywords, mult = item
        KEYWORD_MULTIPLIER_MAP[tuple(keywords)] = mult
        updated += 1
    if updated:
        logging.info("Applied %d keyword_overrides from %s.", updated, path)

    # 3) target_units: dict of {product_lv1: unit}
    tu = data.get("target_units", {})
    if tu:
        TARGET_UNIT_BY_TECH.update({k.lower(): v for k, v in tu.items()})
        logging.info("Updated target units for %d technologies.", len(tu))

## ========= 1 Extract Capacity Info =========
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
            scl = SCALE_MAP.get(suffix.lower())
            if scl:
                return value, scl, remaining.strip()
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

## ========= 2 Apply Capacity Normalisation =========
# ---------- GWh converter -------------------------------------------------
def normalize_to_gwh_and_flag(row, conversion=False, *, multiplier_override: int | None = None):
    """
    Normalises capacity to GWh (per year), applying product-specific multipliers when requested.
    Returns: (capacity_normalised, flag_failed, metric_out, flag_conversion)
    """
    value  = row.get("capacity_value")
    scale  = row.get("capacity_scale", 1)
    metric = row.get("capacity_metric")
    time   = row.get("capacity_time")

    if value is None or metric is None or not isinstance(metric, str):
        return None, True, None, bool(conversion)
    if pd.isna(scale):
        scale = 1

    # 1) scale
    scaled = apply_scale(value, scale)
    if has_nan(scaled):
        return None, True, None, bool(conversion)

    # 2) annualize (rate → per year)
    annual = annualize(scaled, time)
    if has_nan(annual):
        return None, True, None, bool(conversion)

    # 3) choose multiplier (single place)
    if multiplier_override is not None:
        mult = float(multiplier_override)
    else:
        mult = 5e-6 if conversion else 1.0

    # 4) apply multiplier once
    out = multiply_vals(annual, mult)
    if has_nan(out):
        return None, True, None, bool(conversion)

    return out, False, "gigawatt hour", bool(conversion)

def normalize_to_vehicle_and_flag(row, conversion=False):
    """
    Converts capacity → vehicles/year.
    Returns: capacity_normalised, flag_failed, metric_out, conversion
    """
    value  = row.get("capacity_value")
    scale  = row.get("capacity_scale", 1)
    metric = row.get("capacity_metric")
    time   = row.get("capacity_time")

    if value is None or metric is None or not isinstance(metric, str):
        return None, True, None, False
    if pd.isna(scale):
        scale = 1

    scaled = apply_scale(value, scale)
    if has_nan(scaled):
        return None, True, None, False

    annual = annualize(scaled, time)
    if has_nan(annual):
        return None, True, None, False

    return annual, False, "vehicle", bool(conversion)

def metric_is_missing(metric):
    """
    True when metric is None/NaN/empty/'nan'/'none'/'unit' (case-insensitive).
    """
    if metric is None:
        return True
    try:
        if pd.isna(metric):
            return True
    except Exception:
        pass
    return str(metric).strip().lower() in {"", "nan", "none", "unit"}

def normalize_default(row):
    """
    Annualize a numeric capacity using the row's scale and time.
    Returns: capacity_normalised, flag_failed, capacity_metric_normalized, flag_conversion(False)
    """
    value  = row.get("capacity_value")
    scale  = row.get("capacity_scale", 1)
    metric = row.get("capacity_metric")
    time   = row.get("capacity_time")

    # validation
    if value is None or metric is None or not isinstance(metric, str):
        return None, True, None, False
    if pd.isna(scale):
        scale = 1

    # scale then annualize
    scaled = apply_scale(value, scale)
    if scaled is None:
        return None, True, None, False

    annual = annualize(scaled, time)    
    if has_nan(annual):
        return None, True, None, False

    metric_lower = metric.strip().lower()
    return annual, False, metric_lower, False

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

    # ---- 1) Metric explicitly gigawatt → normalize_default (annualize) ----
    if "gigawatt" in metric_str:
        value, failed, metric_out, conv = normalize_default(row)
        return value, failed, metric_out, conv, "default:metric-is-gigawatt"

    # ---- 2) Explicit multiplier override for (lv1, lv2, metric) ----
    mult_override, key = get_explicit_override(product_lv1, product_lv2, metric_str)
    if mult_override is not None:
        value, failed, metric_out, conv = normalize_to_gwh_and_flag(
            row, conversion=False, multiplier_override=mult_override
        )
        tag = f"override:{key[0]}/{key[1] or '-'}:{key[2] or '-'}"
        return value, failed, metric_out, conv, tag

    # ---- 3) VEHICLE rows with missing/placeholder metric ----
    if product_lv1 == "vehicle":
        if metric_is_missing(metric_raw) or metric_str == "unit":
            value, failed, metric_out, conv = normalize_to_vehicle_and_flag(row, conversion=False)
            return value, failed, metric_out, conv, "vehicle:units-or-missing"

    # ---- 4) BATTERY special cases ----

    # 4a) battery + eam + missing metric + EV keyword → keyword override
    if product_lv1 == "battery" and product_lv2 == "eam" and metric_is_missing(metric_raw):
        if not any(exc in text for exc in excludes):
            override, matched, keywords = detect_keyword_multiplier(text)
            if override is not None:
                value, failed, metric_out, conv = normalize_to_gwh_and_flag(
                    row, conversion=True, multiplier_override=override
                )
                return value, failed, metric_out, conv, f"battery-keyword:eam:{matched}"

    # 4b) battery OR metric=='unit' + EV keyword → keyword override
    if product_lv1 == "battery" or metric_str == "unit":
        if not any(exc in text for exc in excludes):
            override, matched, keywords = detect_keyword_multiplier(text)
            if override is not None:
                value, failed, metric_out, conv = normalize_to_gwh_and_flag(
                    row, conversion=True, multiplier_override=override
                )
                return value, failed, metric_out, conv, f"battery-keyword:{matched}"

        # 4c) battery + missing metric → fallback override (Case 1)
        if metric_is_missing(metric_raw):
            fallback_override = MULTIPLIER_OVERRIDE_MAP.get(("battery", None, None))
            value, failed, metric_out, conv = normalize_to_gwh_and_flag(
                row, conversion=True, multiplier_override=fallback_override
            )
            return value, failed, metric_out, conv, "battery:fallback-missing-metric"

        # 4d) battery + metric present → to GWh without keyword conversion
        value, failed, metric_out, conv = normalize_to_gwh_and_flag(row, conversion=False)
        return value, failed, metric_out, conv, "battery:metric-present"

    # ---- 5) Fallback → normalize_default ----
    value, failed, metric_out, conv = normalize_default(row)
    return value, failed, metric_out, conv, "fallback:normalize-default"

# ========= Pipeline Execution =========
def run_capacity_normalisation_pipeline(file_path=FACTORY_TECH):
    # EDITED - reading a df not file_path
    load_capacity_rule_overrides()
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

    # 4) Normalize (now returns FIVE values incl. normalization_case)
    df[[
        "capacity_normalized",
        "flag_failed",
        "capacity_metric_normalized",
        "flag_conversion",
        "normalization_case"
    ]] = df.apply(lambda row: pd.Series(capacity_logic(row)), axis=1)

    # ---- Logging summary (add it right here) ----
    total = len(df)
    failed = int(df["flag_failed"].fillna(False).sum())
    pct = (failed / total * 100.0) if total else 0.0
    logging.info("Capacity rows: %d | failed: %d (%.1f%%)", total, failed, pct)

    # Which branches fired
    logging.info(df["normalization_case"].value_counts(dropna=False).to_string())

    columns_capacity_debug = ["capacity", "product", "product_lv1", "product_lv2", "capacity_value", "capacity_scale", "capacity_text",
               "capacity_metric", "capacity_time", "capacity_normalized", "capacity_metric_normalized",
               "flag_failed", "flag_conversion", "normalization_case"]
    
    df[columns_capacity_debug].to_excel(FACTORY_TECH_CLEAN_CAPACITIES)

    return df

# ========= Main Run Block =========
if __name__ == "__main__":
    file_path = 'storage/output/clean_output_ben.xlsx'
    df_result = run_capacity_normalisation_pipeline(file_path)
    output_path = 'storage/output/clean_output_capacity.xlsx'
    df_result.to_excel(output_path, index=False)
    logging.info(df_result.head(10))

