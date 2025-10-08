import logging

def log_nodes_for_article(ctx: tuple, article_id: int | str):
    """
    Log all nodes (by label) that belong to a given article_id.

    Parameters
    ----------
    ctx : tuple
        Output of make_context_from_frames -> (nodes_by_label, rels_by_label, geo_lookup)
    article_id : int | str
        The article ID to filter by
    """
    nodes_by_label, _, _ = ctx  # unpack only what we need

    for label, df in nodes_by_label.items():
        if "article_id" not in df.columns:
            continue
        subset = df[df["article_id"] == article_id]
        if not subset.empty:
            logging.info(f"--- {label} ({len(subset)} rows) ---")
            logging.info(subset[["name", "label"]].to_string(index=False))