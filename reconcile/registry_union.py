# src/build_registry_union.py
import logging
import pandas as pd

from src.merge_specifications import (
    FACTORY_REGISTRY_DIRECT, FACTORY_REGISTRY_CAP, FACTORY_REGISTRY_INV
)
from merge import run_view
from src.config import FACTORY_REGISTRY  # final output excel (if you still want it)
from src.inputs import EUROPEAN_COUNTRIES

PROVENANCE_ORDER = ["direct", "inferred_capacity", "inferred_investment"]

def _add_provenance(df: pd.DataFrame, tag: str) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["provenance"] = tag
    return out

def build_registry_union(to_excel: bool = True) -> pd.DataFrame:

    logging.info("🏭 Building registry union (direct + capacity + investment)…")
    
    # 1) Build three small views
    df_direct = run_view(FACTORY_REGISTRY_DIRECT, out_path=None)
    df_cap    = run_view(FACTORY_REGISTRY_CAP,    out_path=None)
    df_inv    = run_view(FACTORY_REGISTRY_INV,    out_path=None)

    df_direct = _add_provenance(df_direct, "direct")
    df_cap    = _add_provenance(df_cap,    "inferred_capacity")
    df_inv    = _add_provenance(df_inv,    "inferred_investment")

    # 2) Union
    df = pd.concat([df_direct, df_cap, df_inv], ignore_index=True)

    # 3) Deduplicate with clear precedence
    #    Key that makes sense before grouping: (factory, inst_canon, iso2, adm1, product_lv1, product_lv2)
    #    If duplicates exist, keep the row with the best provenance by PROVENANCE_ORDER.
    if not df.empty:
        df["provenance_rank"] = df["provenance"].map({p:i for i,p in enumerate(PROVENANCE_ORDER)})
        dedupe_key = ["factory","inst_canon","iso2","adm1","product_lv1","product_lv2"]
        df = (df.sort_values(dedupe_key + ["provenance_rank"])
                .drop_duplicates(dedupe_key, keep="first")
                .drop(columns=["provenance_rank"]))
    else:
        logging.warning("Registry union produced no rows.")

    # 4) (Optional) Save the union as the new FACTORY_REGISTRY input to grouping
    if to_excel:
        df.to_excel(FACTORY_REGISTRY, index=False)
        logging.info(f"💾 Saved registry union to {FACTORY_REGISTRY}")

    return df