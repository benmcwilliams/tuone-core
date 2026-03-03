import logging

def log_nodes_for_article(ctx: tuple, article_id: int | str):
    """
    Log all nodes (by label) that belong to a given article_id.
    When a debug tracker is set for this article, writes to the per-article log file only; otherwise no-op (no main console output).
    """
    from src.debug_helpers import get_debug_tracker

    nodes_by_label, _, _ = ctx  # unpack only what we need
    tracker = get_debug_tracker()
    use_tracker = tracker is not None and tracker.article_id == str(article_id)

    for label, df in nodes_by_label.items():
        if "article_id" not in df.columns:
            continue
        subset = df[df["article_id"] == article_id]
        if not subset.empty and use_tracker:
            tracker.info("--- %s (%d rows) ---", label, len(subset))
            tracker.info("%s", subset[["name", "label"]].to_string(index=False))