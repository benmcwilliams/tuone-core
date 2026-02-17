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

def build_registry_union(to_excel: bool = True, *, context=None, debug_article_id: str | None = None) -> pd.DataFrame:

    logging.info("🏭 Building registry union (direct + capacity + investment)…")
    
    # 1) Build three small views
    df_direct = run_view(FACTORY_REGISTRY_DIRECT, out_path=None, context=context)
    df_cap    = run_view(FACTORY_REGISTRY_CAP,    out_path=None, context=context)
    df_inv    = run_view(FACTORY_REGISTRY_INV,    out_path=None, context=context)

    df_direct = _add_provenance(df_direct, "direct")
    df_cap    = _add_provenance(df_cap,    "inferred_capacity")
    df_inv    = _add_provenance(df_inv,    "inferred_investment")

    if debug_article_id and not df_direct.empty and "article_id" in df_direct.columns:
        sub = df_direct[df_direct["article_id"] == debug_article_id]
        cols = [c for c in ["iso2", "city_key", "adm1"] if c in sub.columns]
        sample = sub[cols].head(3).to_dict("records") if not sub.empty and cols else None
        logging.info(
            "[DEBUG registry] DIRECT view: article %s rows=%d; sample=%s",
            debug_article_id,
            len(sub),
            sample,
        )

    # 2) Union
    df = pd.concat([df_direct, df_cap, df_inv], ignore_index=True)

    # 3) Deduplicate with clear precedence (per article: same facility in multiple articles keeps one row per article)
    #    Key: (article_id, factory, inst_canon, iso2, adm1, product_lv1, product_lv2). Best provenance wins per key.
    if not df.empty:
        df["provenance_rank"] = df["provenance"].map({p:i for i,p in enumerate(PROVENANCE_ORDER)})
        dedupe_key = ["article_id", "factory", "factory_status", "inst_canon", "iso2", "adm1", "product_lv1", "product_lv2"]
        df = (df.sort_values(dedupe_key + ["provenance_rank"])
                .drop_duplicates(dedupe_key, keep="first")
                .drop(columns=["provenance_rank"]))
    else:
        logging.warning("Registry union produced no rows.")

    if debug_article_id and not df.empty and "article_id" in df.columns:
        sub = df[df["article_id"] == debug_article_id]
        logging.info(
            "[DEBUG registry] After union+dedupe: article %s rows=%d",
            debug_article_id,
            len(sub),
        )

    # 4) (Optional) Save the union as the new FACTORY_REGISTRY input to grouping
    if to_excel:
        df.to_excel(FACTORY_REGISTRY, index=False)
        logging.info(f"💾 Saved registry union to {FACTORY_REGISTRY}")

    return df