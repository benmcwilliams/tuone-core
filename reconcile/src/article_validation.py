# src/article_validation.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, Iterable
from mongo_client import articles_collection

def build_article_validation_map() -> Dict[str, bool]:
    """
    Return {article_id -> validated_bool}.
    'validation' is True (legacy) or a timestamp (int/float).
    Anything else -> False.
    """
    vmap: Dict[str, bool] = {}
    for doc in articles_collection.find({}, {"_id": 1, "validation": 1}):
        aid = str(doc["_id"])
        val = doc.get("validation")
        vmap[aid] = (val is True) or isinstance(val, (int, float))
    return vmap

def compute_validated_flag(article_ids: Iterable[str] | None, vmap: Dict[str, bool]) -> bool:
    """
    If you ever end up with more than one article_id per event (e.g., after merges),
    this returns True if ANY of them are validated. For the current pipeline (one id),
    this is equivalent to a simple lookup.
    """
    if not article_ids:
        return False
    return any(bool(vmap.get(aid, False)) for aid in article_ids)