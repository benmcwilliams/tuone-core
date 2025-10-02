# src/admin_levels.py
import logging
import pandas as pd

# Which admin level to use per ISO2. You can set a single level or a fallback list.
# Examples:
#   "DE": "adm2"   -> always use adm2 for Germany
#   "HU": ["adm2","adm1"] -> try adm2, fallback to adm1 if adm2 is null
ADMIN_LEVEL_BY_ISO2: dict[str, str | list[str]] = {
    "AT": ["adm3", "adm2"],
    "BE": "adm3",
    "BG": ["adm2", "adm1"],
    "CZ": ["adm3", "adm1"], # Prague only has adm1...
    "DE": "adm4",
    "HU": "adm1",
    "HR": "adm1",
    "FI": "adm3",
    "FR": "adm4",
    "GB": "adm2",   # England/Scotland/Wales/N.I. at adm2
    "IE": "adm2",
    "IT": "adm3",
    "LU": "adm2",
    "NL": "adm2",
    "PL": "adm3", 
    "SE": "adm2",
}

DEFAULT_LEVELS: list[str] = ["adm1"]  # fallback when ISO2 not listed

def _levels_for_iso2(iso2: str) -> list[str]:
    rule = ADMIN_LEVEL_BY_ISO2.get(iso2)
    if rule is None:
        return DEFAULT_LEVELS
    return [rule] if isinstance(rule, str) else list(rule)

def add_admin_group_key(df: pd.DataFrame,
                        out_col: str = "admin_group_key",
                        log: bool = True) -> pd.DataFrame:
    """
    Create a single column to use for grouping, choosing the appropriate
    admin level per ISO2 according to ADMIN_LEVEL_BY_ISO2 (with fallbacks).
    Does not modify original adm* columns.
    """
    if out_col in df.columns:
        df = df.drop(columns=[out_col])

    # Build the chosen key row-by-row based on country rule
    def pick_key(row) -> str | None:
        iso2 = row.get("iso2")
        if pd.isna(iso2):
            return None
        for col in _levels_for_iso2(str(iso2)):
            val = row.get(col)
            if pd.notna(val) and str(val).strip():
                return str(val).strip()
        # final fallback: use adm1 if present
        val = row.get("adm1")
        return str(val).strip() if pd.notna(val) and str(val).strip() else None

    df[out_col] = df.apply(pick_key, axis=1)

    if log:
        missing = df[out_col].isna().sum()
        if missing:
            logging.info(f"⚠️ {missing} rows lack an admin_group_key after applying per-country rules.")

    return df