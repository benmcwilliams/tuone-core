#!/usr/bin/env python3
"""
Lightweight validation for government KG routing + config (no Mongo/OpenAI).
Run from repo: python3 kg_builder/test_gov_validation.py
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def get_article_domain(article: dict) -> str:
    """Mirror of kg_builder/main.get_article_domain for offline checks."""
    tag = article.get("meta", {}).get("tag")
    if tag == "government":
        return "government"
    return "investment"


def main() -> int:
    try:
        import yaml  # type: ignore
    except ImportError:
        print("SKIP: PyYAML not installed", file=sys.stderr)
        return 0

    cfg = yaml.safe_load((ROOT / "extraction_config.yaml").read_text(encoding="utf-8"))
    assert "gov_entities" in cfg and "gov_relationships" in cfg
    for key in ("gov_entities", "gov_relationships"):
        for field in ("prompt", "schema", "function_name", "top_key", "model_key"):
            assert field in cfg[key], f"missing {field} in {key}"

    for name in ("gov_entities.json", "gov_relationships.json"):
        json.loads((ROOT / "src/schemas" / name).read_text(encoding="utf-8"))

    assert get_article_domain({}) == "investment"
    assert get_article_domain({"meta": {"tag": "government"}}) == "government"
    assert get_article_domain({"meta": {"tag": "investment"}}) == "investment"

    print("gov validation OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
