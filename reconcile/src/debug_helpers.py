import logging
from typing import List, Optional

import pandas as pd


def debug_print_df(
    df: pd.DataFrame,
    label: str,
    cols: List[str],
    debug_article_id: Optional[str],
) -> None:
    """
    Log a compact view of rows for a single article_id in debug mode.

    - If debug_article_id is None, this is a no-op.
    - If the DataFrame has no article_id column, logs a short note and returns.
    - Only prints selected columns that are actually present in the DataFrame.
    """
    if not debug_article_id:
        return

    if "article_id" not in df.columns:
        logging.info(
            f"[DEBUG {label}] article_id={debug_article_id}: 'article_id' column missing"
        )
        return

    sub = df.loc[df["article_id"] == debug_article_id].copy()
    if sub.empty:
        logging.info(
            f"[DEBUG {label}] article_id={debug_article_id}: no rows in this frame"
        )
        return

    # Keep only requested columns that exist
    existing_cols = [c for c in cols if c in sub.columns]
    if existing_cols:
        sub = sub[existing_cols]

    logging.info(
        f"[DEBUG {label}] article_id={debug_article_id} "
        f"({len(sub)} rows):\n{sub.to_string(index=False)}"
    )

