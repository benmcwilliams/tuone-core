"""
Shared module for node-mentions extraction (rule-based matching, no LLM).
Used by the standalone run_mentions script. Does not depend on main.py.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

# Which node types use which field for matching in text
MATCH_BY_NAME = {"company", "joint_venture", "product", "grantor", "government"}
MATCH_BY_AMOUNT = {"capacity", "investment", "aid", "tax_cut", "support_package"}
MATCH_BY_CITY = {"factory"}


def _normalize_paragraphs(paragraphs: list[dict] | dict) -> list[dict]:
    """
    Normalize paragraphs to a list of one para-object.
    Accepts: [{"p0": "...", "p1": "..."}] (list) or {"p0": "...", "p1": "..."} (dict).
    """
    if not paragraphs:
        return []
    if isinstance(paragraphs, dict):
        return [paragraphs]
    if isinstance(paragraphs, list) and paragraphs and isinstance(paragraphs[0], dict):
        return paragraphs
    return []


def _get_search_strings_for_node(node: dict) -> list[str]:
    """
    Return list of strings to search for in text, depending on node type.
    Empty list means skip this node.
    """
    if not isinstance(node, dict):
        return []
    node_type = (node.get("type") or "").strip().lower().replace(" ", "_")

    if node_type in MATCH_BY_NAME:
        name = (node.get("name") or "").strip()
        canon = node.get("name_canon")
        if isinstance(canon, str):
            canon = canon.strip()
        else:
            canon = ""
        out = []
        if name:
            out.append(name)
        if canon and canon != name:
            out.append(canon)
        return out

    if node_type in MATCH_BY_AMOUNT:
        amount = node.get("amount")
        if amount is None:
            return []
        s = str(amount).strip()
        return [s] if s else []

    if node_type in MATCH_BY_CITY:
        loc = node.get("location")
        if not isinstance(loc, dict):
            return []
        city = (loc.get("city") or "").strip()
        # Treat string "null" / "none" as missing (e.g. from DB or LLM output)
        if city and city.lower() not in ("null", "none"):
            return [city]
        # Fallback to country if city is null/empty or the literal "null"
        country = (loc.get("country") or "").strip()
        if country and country.lower() not in ("null", "none"):
            return [country]
        return []

    return []


def _find_spans(text: str, search_string: str, use_word_boundaries: bool = True) -> list[tuple[int, int]]:
    """
    Find matches in text; return (start, end) pairs.
    If use_word_boundaries=True, uses word boundaries (for names/cities).
    If False, matches exact string (for amounts with currency symbols).
    Case-insensitive.
    """
    if not search_string:
        return []
    if use_word_boundaries:
        pattern = r"\b" + re.escape(search_string) + r"\b"
    else:
        pattern = re.escape(search_string)
    return [(m.start(), m.end()) for m in re.finditer(pattern, text, re.IGNORECASE)]


def extract_mentions_by_matching(
    paragraphs: list[dict] | dict,
    nodes: list[dict],
) -> list[dict]:
    """
    Rule-based mention extraction: match name / amount / city per node type.
    Returns list of {node_id, para_ref, char_start, char_end}; deduped.
    """
    para_list = _normalize_paragraphs(paragraphs)
    if not para_list or not nodes:
        return []
    para_obj = para_list[0]
    mentions: list[dict] = []
    seen: set[tuple[str, str, int, int]] = set()

    for para_ref in sorted(para_obj.keys()):
        text = para_obj[para_ref] or ""
        for node in nodes:
            nid = node.get("id")
            if not nid:
                continue
            node_type = (node.get("type") or "").strip().lower().replace(" ", "_")
            # Amount-based nodes (capacity, investment, aid) don't use word boundaries
            # because amounts often start with currency symbols (£, €, $) which are non-word
            use_word_boundaries = node_type not in MATCH_BY_AMOUNT
            for s in _get_search_strings_for_node(node):
                for start, end in _find_spans(text, s, use_word_boundaries=use_word_boundaries):
                    key = (nid, para_ref, start, end)
                    if key in seen:
                        continue
                    seen.add(key)
                    mentions.append({
                        "node_id": nid,
                        "para_ref": para_ref,
                        "char_start": start,
                        "char_end": end,
                    })
    return mentions


def _parse_ts(value: str | int | float | None) -> datetime | None:
    """Parse a timestamp to UTC datetime. Returns None if missing or invalid."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OSError, ValueError):
            return None
    if isinstance(value, str):
        try:
            # ISO format
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None
    return None


def should_run_mentions(article: dict) -> bool:
    """
    Return True if we should run mentions extraction for this article.
    Run when: no mentions_ts, or llm_processed.ts or validation/boiler is after mentions_ts,
    or mentions_ts exists but mentions is missing or empty.
    """
    if not article.get("nodes") or not article.get("paragraphs"):
        return False

    mentions_ts = article.get("mentions_ts")
    mentions = article.get("mentions")
    if mentions_ts and (not mentions or (isinstance(mentions, list) and len(mentions) == 0)):
        return True
    if not mentions_ts:
        return True

    mentions_dt = _parse_ts(mentions_ts)
    if mentions_dt is None:
        return True

    llm_ts = article.get("llm_processed", {}) or {}
    if isinstance(llm_ts, dict):
        llm_dt = _parse_ts(llm_ts.get("ts"))
        if llm_dt is not None and llm_dt > mentions_dt:
            return True

    val = article.get("validation")
    if val is True:
        pass  # do not use as timestamp
    else:
        val_dt = _parse_ts(val)
        if val_dt is not None and val_dt > mentions_dt:
            return True

    # meta.boiler_markers_backfilled_at (BSON date from MongoDB) newer than mentions_ts
    boiler = (article.get("meta") or {}).get("boiler_markers_backfilled_at")
    if boiler is not None and isinstance(boiler, datetime):
        if boiler.tzinfo is None:
            boiler = boiler.replace(tzinfo=timezone.utc)
        if boiler > mentions_dt:
            return True

    return False


def run_mentions_extraction(
    paragraphs: list[dict] | dict,
    nodes: list[dict],
    logger: logging.Logger,
) -> list[dict]:
    """
    Rule-based mention extraction: match name / amount / city per node type.
    Returns list of {node_id, para_ref, char_start, char_end}. Logger is unused but kept for API compatibility.
    """
    return extract_mentions_by_matching(paragraphs, nodes)
