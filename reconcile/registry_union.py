# src/build_registry_union.py
import logging
import pandas as pd

from src.merge_specifications import (
    FACTORY_REGISTRY_DIRECT, FACTORY_REGISTRY_CAP, FACTORY_REGISTRY_INV
)
from merge import run_view
from src.config import FACTORY_REGISTRY  # final output excel (if you still want it)
from src.inputs import EUROPEAN_COUNTRIES
from src.debug_helpers import get_debug_tracker

PROVENANCE_ORDER = ["direct", "inferred_capacity", "inferred_investment"]

def _add_provenance(df: pd.DataFrame, tag: str) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["provenance"] = tag
    return out

def build_registry_union(to_excel: bool = True, *, context=None, debug_article_id: str | None = None) -> pd.DataFrame:

    logging.info("🏭 Building registry union (direct + capacity + investment)…")
    tracker = get_debug_tracker()
    use_debug = tracker is not None and debug_article_id and tracker.article_id == debug_article_id

    # 1) Build three small views (view_name used for per-join diagnostics in merge)
    df_direct = run_view(FACTORY_REGISTRY_DIRECT, out_path=None, context=context, view_name="FACTORY_REGISTRY_DIRECT")
    df_cap    = run_view(FACTORY_REGISTRY_CAP,    out_path=None, context=context, view_name="FACTORY_REGISTRY_CAP")
    df_inv    = run_view(FACTORY_REGISTRY_INV,    out_path=None, context=context, view_name="FACTORY_REGISTRY_INV")

    df_direct = _add_provenance(df_direct, "direct")
    df_cap    = _add_provenance(df_cap,    "inferred_capacity")
    df_inv    = _add_provenance(df_inv,    "inferred_investment")

    if use_debug:
        tracker.section("Registry union: per-view row counts for article")
        for name, frame in [("direct", df_direct), ("inferred_capacity", df_cap), ("inferred_investment", df_inv)]:
            n = len(frame[frame["article_id"] == debug_article_id]) if not frame.empty and "article_id" in frame.columns else 0
            tracker.checkpoint("registry_" + name, n)
            if n > 0 and "iso2" in frame.columns:
                iso2_vals = frame.loc[frame["article_id"] == debug_article_id, "iso2"].dropna().unique().tolist()
                tracker.info("  iso2 values: %s", iso2_vals)

    # 2) Union
    df = pd.concat([df_direct, df_cap, df_inv], ignore_index=True)

    # 3) Deduplicate with clear precedence (per article: same facility in multiple articles keeps one row per article)
    #    Key: (article_id, factory, inst_canon, iso2, adm1, product_lv1, product_lv2, product_lv3). Best provenance wins per key.
    if not df.empty:
        if "product_lv3" not in df.columns:
            df["product_lv3"] = None
        df["provenance_rank"] = df["provenance"].map({p:i for i,p in enumerate(PROVENANCE_ORDER)})
        dedupe_key = ["article_id", "factory", "factory_status", "inst_canon", "iso2", "adm1", "product_lv1", "product_lv2", "product_lv3"]
        df = (df.sort_values(dedupe_key + ["provenance_rank"])
                .drop_duplicates(dedupe_key, keep="first")
                .drop(columns=["provenance_rank"]))
    else:
        logging.warning("Registry union produced no rows.")

    if use_debug:
        n_after = len(df[df["article_id"] == debug_article_id]) if not df.empty and "article_id" in df.columns else 0
        tracker.checkpoint("registry_union_after_dedupe", n_after)
        if n_after == 0:
            tracker.drop_reason(
                "registry_union",
                "no rows for this article in the facility registry",
                "All three views (direct, capacity-inferred, investment-inferred) contributed 0 rows for this article after join chain and EU filter. Typical causes: no ownership (owns) edge for EU factories, or facilities only in non-EU countries.",
            )

    # 4) (Optional) Save the union as the new FACTORY_REGISTRY input to grouping
    if to_excel:
        df.to_excel(FACTORY_REGISTRY, index=False)
        logging.info(f"💾 Saved registry union to {FACTORY_REGISTRY}")

    return df