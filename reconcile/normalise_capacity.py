import sys; sys.path.append("..")
from pathlib import Path
import pandas as pd

import logging
from reconcile.src.parse_capacity_text import parse_capacity_text
from reconcile.src.normalise_time_units import extract_normalized_time_unit
from reconcile.src.normalise_capacity_units import normalise_capacity_unit
from reconcile.src.capacity_constants import MULTIPLIER_OVERRIDE_MAP, KEYWORD_MULTIPLIER_MAP
from reconcile.src.capacity_helpers import load_capacity_column, apply_scale, annualize, multiply_vals, has_nan, get_explicit_override, detect_keyword_multiplier, metric_is_missing
from src.config import FACTORY_TECH, FACTORY_TECH_CLEAN_CAPACITIES

# Avoid duplicate handlers if this file is re-imported
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(message)s")

# ---------- GWh converter -------------------------------------------------
def normalize_to_gwh_and_flag(row, conversion=False, *, multiplier_override: int | None = None):
    """
    Normalises capacity to GWh (per year), applying product-specific multipliers when requested.
    Returns: (capacity_normalised, flag_failed, metric_out, flag_conversion)
    """
    value  = row.get("raw_value")
    scale  = row.get("apply_scale", 1)
    metric = row.get("unit")
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
    value  = row.get("raw_value")
    scale  = row.get("apply_scale", 1)
    metric = row.get("unit")
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

def normalize_default(row):
    """
    Annualize a numeric capacity using the row's scale and time.
    Returns: capacity_normalised, flag_failed, capacity_metric_normalized, flag_conversion(False)
    """
    value  = row.get("raw_value")
    scale  = row.get("apply_scale", 1)
    metric = row.get("unit")
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
    1. If capacity_metric contains 'gigawatt' → normalize_default (annualize, keep metric) | adjust to be based on product_lv1 / product_lv2
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

    metric_raw = row.get("unit")
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

    df = load_capacity_column(file_path)

    # a) extract numeric value | scale | remaining text from raw_capacity_text
    df[["raw_value", "text_scalar", "capacity_text"]] = df["capacity"].apply(
        lambda x: pd.Series(parse_capacity_text(x))
    )

    # b) normalised units and scale adjustment (e.g. kilotonne → tonne + 1e3 scale)
    df[["unit", "capacity_text", "metric_scale"]] = df["capacity_text"].apply(
        lambda x: pd.Series(normalise_capacity_unit(x))
    )

    # c) calculate scale to be applied (text scalar, eg Bn = billions, multiple by unit scale, eg kwh to gwh)
    df["apply_scale"] = df["text_scalar"].fillna(1) * df["metric_scale"].fillna(1)
    #df.drop(columns=["metric_scale"], inplace=True)

    # d) time units (e.g. per year)
    df[["capacity_time", "capacity_text"]] = df["capacity_text"].apply(
        lambda x: pd.Series(extract_normalized_time_unit(x))
    )

    # MAIN normalisation (now returns FIVE values incl. normalization_case)
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

    debug_cols = ["capacity", "raw_value", "unit", "product", "product_lv1", "product_lv2", 
                  "text_scalar", "metric_scale", "apply_scale",
                  "capacity_text","capacity_time", "capacity_normalized", "capacity_metric_normalized",
                "flag_failed", "flag_conversion", "normalization_case"
    ]
    df[debug_cols].to_excel(FACTORY_TECH_CLEAN_CAPACITIES)
    return df

# debug helper
def trace_one(row_idx: int = 0, file_path: str = FACTORY_TECH):
    """
    Trace end-to-end normalisation for a single row by index.
    Logs: raw capacity, parsed value/scale/text, metric(+scale), time, and final capacity_logic output.
    Returns the 5‑tuple from capacity_logic.
    """
    # Load data
    df = load_capacity_column(file_path)
    n = len(df)
    if n == 0:
        logging.error("Dataframe is empty from %s.", file_path)
        return None
    if row_idx < 0 or row_idx >= n:
        logging.error("row_idx %d out of range (0..%d).", row_idx, n - 1)
        return None

    row = df.iloc[row_idx].to_dict()

    # A. Raw input
    logging.info("===== TRACE row %d =====", row_idx)
    logging.info("product_lv1=%r product_lv2=%r", row.get("product_lv1"), row.get("product_lv2"))
    logging.info("raw capacity=%r", row.get("capacity"))

    # B. Parse numeric + remainder
    val, scale, rem = parse_capacity_text(row.get("capacity"))
    logging.info("parse_capacity_text -> value=%s scale=%s rem=%r", val, scale, rem)

    # C. Metric (+metric_scale) from remainder
    metric, rem2, metric_scale = normalise_capacity_unit(rem)
    logging.info("extract_normalized_metric_unit -> metric=%r metric_scale=%s rem=%r", metric, metric_scale, rem2)

    # D. Time unit from remainder
    time_unit, rem3 = extract_normalized_time_unit(rem2)
    logging.info("extract_normalized_time_unit -> time=%r rem=%r", time_unit, rem3)

    # E. Build the row exactly like the pipeline does (including merged scale)
    merged_scale = (1 if scale is None else scale) * (1 if metric_scale is None else metric_scale)
    routed_row = {
        **row,
        "raw_value": val,
        "capacity_scale": merged_scale,
        "capacity_text": rem2,          # note: after metric removal (matches pipeline order)
        "unit": metric,
        "capacity_time": time_unit,
    }

    # F. Route through main logic
    out = capacity_logic(routed_row)

    # G. Pretty log of the result (works whether you return a tuple or a dataclass)
    try:
        value, failed, metric_out, conversion, case = out
        logging.info(
            "capacity_logic -> value=%s failed=%s metric_out=%r conversion=%s case=%r",
            value, failed, metric_out, conversion, case
        )
    except Exception:
        logging.info("capacity_logic -> %r", out)

    return out

# ========= Main Run Block =========
if __name__ == "__main__":
    trace_one(78, 'storage/output/factory-technological.xlsx')
    # file_path = 'storage/output/clean_output_ben.xlsx'
    # df_result = run_capacity_normalisation_pipeline(file_path)
    # output_path = 'storage/output/clean_output_capacity.xlsx'
    # df_result.to_excel(output_path, index=False)
    # logging.info(df_result.head(10))

