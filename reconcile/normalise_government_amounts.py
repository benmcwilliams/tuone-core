import re
from pathlib import Path
from functools import lru_cache

import pandas as pd


PERCENT_RE = re.compile(r"(%|\\bper\\s*cent\\b)", re.IGNORECASE)
CENT_PER_LITRE_RE = re.compile(r"\\bcents?\\b\\s*(per\\s*)?\\blitre\\b", re.IGNORECASE)
CENT_ONLY_RE = re.compile(r"\\bcents?\\b", re.IGNORECASE)


@lru_cache(maxsize=1)
def _load_investment_parser_funcs():
    """
    Load parsing helpers from normalise_investment.py without executing
    the bottom example-call block.
    """
    src_path = Path(__file__).resolve().parent / "normalise_investment.py"
    source = src_path.read_text(encoding="utf-8")
    source = source.split("# ======= Example call =======")[0]
    ns = {}
    exec(source, ns)
    return {
        "_preclean_investment_text": ns["_preclean_investment_text"],
        "detect_currency_iso": ns["detect_currency_iso"],
        "remove_currency_tokens": ns["remove_currency_tokens"],
        "parse_amount_from_text": ns["parse_amount_from_text"],
        "multiply_vals": ns["multiply_vals"],
    }


def _classify_unit(raw_text: str) -> str:
    text = (raw_text or "").strip()
    if not text:
        return "missing"
    if PERCENT_RE.search(text):
        return "percent"
    if CENT_PER_LITRE_RE.search(text):
        return "cent_per_litre"
    if CENT_ONLY_RE.search(text):
        return "cent"
    return "currency_amount"


def _enrich_amount_column(df: pd.DataFrame, col: str, prefix: str) -> pd.DataFrame:
    funcs = _load_investment_parser_funcs()
    preclean = funcs["_preclean_investment_text"]
    detect_currency_iso = funcs["detect_currency_iso"]
    remove_currency_tokens = funcs["remove_currency_tokens"]
    parse_amount_from_text = funcs["parse_amount_from_text"]
    multiply_vals = funcs["multiply_vals"]

    if col not in df.columns:
        df[col] = ""

    df[col] = df[col].fillna("").astype(str).str.strip()
    df[f"{prefix}_text_clean"] = df[col].apply(preclean)
    df[f"{prefix}_currency_iso"] = df[f"{prefix}_text_clean"].apply(detect_currency_iso)
    df[f"{prefix}_text_no_currency"] = df[f"{prefix}_text_clean"].apply(remove_currency_tokens)

    parsed = df[f"{prefix}_text_no_currency"].apply(parse_amount_from_text)
    df[[f"{prefix}_raw_value", f"{prefix}_amount_scalar", f"{prefix}_parse_remaining"]] = pd.DataFrame(parsed.tolist(), index=df.index)
    df[f"{prefix}_amount_value"] = df.apply(
        lambda r: multiply_vals(r[f"{prefix}_raw_value"], r[f"{prefix}_amount_scalar"]), axis=1
    )

    df[f"{prefix}_unit_type"] = df[col].apply(_classify_unit)
    df[f"{prefix}_parse_ok_amount"] = df[f"{prefix}_amount_value"].notna() | df[f"{prefix}_raw_value"].notna()
    df[f"{prefix}_parse_ok_currency"] = df[f"{prefix}_currency_iso"].notna()

    def _ok_overall(row: pd.Series) -> bool:
        if row[f"{prefix}_unit_type"] in {"missing"}:
            return True
        if row[f"{prefix}_unit_type"] in {"percent", "cent_per_litre", "cent"}:
            return bool(row[f"{prefix}_parse_ok_amount"])
        return bool(row[f"{prefix}_parse_ok_amount"] and row[f"{prefix}_parse_ok_currency"])

    df[f"{prefix}_parse_ok_overall"] = df.apply(_ok_overall, axis=1)

    def _note(row: pd.Series) -> str:
        if row[f"{prefix}_unit_type"] == "missing":
            return "no raw amount provided"
        if row[f"{prefix}_unit_type"] in {"percent", "cent_per_litre", "cent"} and not row[f"{prefix}_parse_ok_currency"]:
            return "unit parsed without currency (expected for rate-style amount)"
        if row[f"{prefix}_parse_ok_amount"] and not row[f"{prefix}_parse_ok_currency"]:
            return "amount parsed but currency not detected"
        if not row[f"{prefix}_parse_ok_amount"]:
            return "amount parsing failed"
        return "ok"

    df[f"{prefix}_parse_note"] = df.apply(_note, axis=1)
    return df


def normalise_government_amounts(df_in: pd.DataFrame) -> pd.DataFrame:
    df = df_in.copy()
    df = _enrich_amount_column(df, "issued_measure_amount_raw", "issued_measure")
    df = _enrich_amount_column(df, "included_tax_amount_raw", "included_tax")
    return df
