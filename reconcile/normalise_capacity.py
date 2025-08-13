import sys; sys.path.append("..")
import pandas as pd

import logging
from reconcile.src.parse_capacity_text import parse_capacity_text
from reconcile.src.normalise_time_units import extract_normalized_time_unit
from reconcile.src.normalise_capacity_units import normalise_capacity_unit
from reconcile.src.capacity_constants import MULTIPLIER_OVERRIDE_MAP, PRODUCT_CONVERSIONS
from reconcile.src.capacity_helpers import (
    load_capacity_column,
    apply_scale,
    annualize,
    multiply_vals,
    has_nan,
    detect_keyword_multiplier,
    metric_is_missing,
    get_default_unit,
)
from src.config import FACTORY_TECH, FACTORY_TECH_CLEAN_CAPACITIES, CAPACITIES_DEBUG
from dataclasses import dataclass

@dataclass
class CapacityResult:
    value: float | None
    failed: bool
    unit: str | None
    converted: bool
    case: str


# ========= Processing capacity logic =========

def normalize_to_target(
    row,
    *,
    target_unit: str,
    multiplier: float | None = None,
    reason: str | None = None,
) -> CapacityResult:
    value  = row.get("raw_value")
    scale  = row.get("apply_scale", 1)
    metric = row.get("unit")
    time   = row.get("capacity_time")

    if value is None or metric is None or not isinstance(metric, str):
        return CapacityResult(None, True, None, False, "normalize:invalid-input")
    if pd.isna(scale):
        scale = 1

    scaled = apply_scale(value, scale)
    if has_nan(scaled):
        return CapacityResult(None, True, None, False, "normalize:scale-nan")

    annual = annualize(scaled, time)
    if has_nan(annual):
        return CapacityResult(None, True, None, False, "normalize:annualize-nan")

    mult = 1.0 if multiplier is None else float(multiplier)
    out = multiply_vals(annual, mult)
    if has_nan(out):
        return CapacityResult(None, True, None, False, "normalize:multiply-nan")

    return CapacityResult(out, False, target_unit, multiplier not in (None, 1.0), f"normalize:{reason or 'none'}")

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
    lv1 = str(row.get("product_lv1", "")).strip().lower()
    lv2 = str(row.get("product_lv2", "")).strip().lower()
    capacity_text_raw = str(row.get("capacity_text", "") or "")
    capacity_text = capacity_text_raw.lower()

    metric_raw = row.get("unit")
    metric = str(metric_raw).strip().lower() if isinstance(metric_raw, str) else ""

    text = (
        capacity_text.replace(",", " ")
        .replace("-", " ")
        .replace("_", " ")
        .strip()
    )

    default_unit = get_default_unit(lv1, lv2)

    # Helpers
    ENERGY_UNITS = {"watt hour","kilowatt hour","megawatt hour","gigawatt hour","wh","kwh","mwh","gwh"}
    def is_energy_metric(m: str | None) -> bool:
        return bool(m) and m.strip().lower() in ENERGY_UNITS

    def default_match():
        return bool(default_unit and metric == default_unit)

    def vehicle_missing():
        return lv1 == "vehicle" and metric_is_missing(metric_raw)
    
    # Rules (ordered)
    if default_match():
        res = normalize_to_target(row, target_unit=default_unit, multiplier=None, reason=f"default:{default_unit}")
        return res.value, res.failed, res.unit, res.converted, res.case

    # 1) Vehicle with missing/placeholder metric → vehicles/year
    if lv1 == "vehicle" and metric_is_missing(metric_raw):
        res = normalize_to_target(row, target_unit="vehicle", multiplier=None, reason="vehicle:missing")
        return res.value, res.failed, res.unit, res.converted, res.case

    # 2) Battery paths
    if lv1 == "battery":

        # 2a) EAM mass → energy (explicit configured conversion)
        conv = PRODUCT_CONVERSIONS.get(("battery","eam"))
        if lv2 == "eam" and conv and metric == conv["from"]:
            res = normalize_to_target(row, target_unit=conv["to"], multiplier=conv["multiplier"], reason="battery:eam:mass->energy")
            return res.value, res.failed, res.unit, res.converted, res.case

        # 2b) Missing/placeholder metric + EV keyword → keyword multiplier to GWh
        if metric_is_missing(metric_raw) or metric == "unit":
            override, matched, _ = detect_keyword_multiplier(text)
            if override:
                res = normalize_to_target(row, target_unit="gigawatt hour", multiplier=override, reason=f"battery:keyword:{matched}")
                return res.value, res.failed, res.unit, res.converted, res.case
            # No keyword → don't invent energy; fall through to fallback

        # 2c) Energy metric present → normalize to GWh (unit normalizer already scaled)
        if is_energy_metric(metric):
            res = normalize_to_target(row, target_unit="gigawatt hour", multiplier=None, reason="battery:energy-metric")
            return res.value, res.failed, res.unit, res.converted, res.case

    # Fallback: just annualize and keep parsed metric (no multiplier)
    metric_lower = (row.get("unit") or "").strip().lower()
    if not metric_lower:
        return None, True, None, False, "fallback:missing-metric"

    res = normalize_to_target(
        row,
        target_unit=metric_lower,
        multiplier=None,
        reason="fallback:keep-metric",
    )
    return res.value, res.failed, res.unit, res.converted, res.case

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

    # ---- Logging summary ----
    total = len(df)
    failed = int(df["flag_failed"].fillna(False).sum())
    pct = (failed / total * 100.0) if total else 0.0
    logging.info("Capacity rows: %d | failed: %d (%.1f%%)", total, failed, pct)

    # which branches fired
    logging.info(df["normalization_case"].value_counts(dropna=False).to_string())

    debug_cols = ["capacity", "raw_value", "unit", "product", "product_lv1", "product_lv2", 
                  "text_scalar", "metric_scale", "apply_scale",
                  "capacity_text","capacity_time", "capacity_normalized", "capacity_metric_normalized",
                "flag_failed", "flag_conversion", "normalization_case"
    ]
    
    df[debug_cols].to_excel(CAPACITIES_DEBUG)
    df.to_excel(FACTORY_TECH_CLEAN_CAPACITIES)
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
    print("===== TRACE row %d =====", row_idx)
    print("product_lv1=%r product_lv2=%r", row.get("product_lv1"), row.get("product_lv2"))
    print("raw capacity=%r", row.get("capacity"))

    # B. Parse numeric + remainder
    val, scale, rem = parse_capacity_text(row.get("capacity"))
    print("parse_capacity_text -> value=%s scale=%s rem=%r", val, scale, rem)

    # C. Metric (+metric_scale) from remainder
    metric, rem2, metric_scale = normalise_capacity_unit(rem)
    print("extract_normalized_metric_unit -> metric=%r metric_scale=%s rem=%r", metric, metric_scale, rem2)

    # D. Time unit from remainder
    time_unit, rem3 = extract_normalized_time_unit(rem2)
    print("extract_normalized_time_unit -> time=%r rem=%r", time_unit, rem3)

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
        print(
            "capacity_logic -> value=%s failed=%s metric_out=%r conversion=%s case=%r",
            value, failed, metric_out, conversion, case
        )
    except Exception:
        print("capacity_logic -> %r", out)

    return out

# ========= Main Run Block =========
if __name__ == "__main__":
    trace_one(16, 'storage/output/factory-technological.xlsx')
    # file_path = 'storage/output/clean_output_ben.xlsx'
    # df_result = run_capacity_normalisation_pipeline(file_path)
    # output_path = 'storage/output/clean_output_capacity.xlsx'
    # df_result.to_excel(output_path, index=False)
    # logging.info(df_result.head(10))

