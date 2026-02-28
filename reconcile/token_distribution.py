"""
Compute token distribution across project summary collections.

Definition of "project summary collection":
- project metadata from facilities
- full text (title + all paragraphs) from all linked articles in articles collection

Data sources:
- MongoDB facilities (via mongo_client.facilities_collection)
- MongoDB articles collection (via mongo_client.articles_collection)

Outputs:
- CSV: per-project token counts
- TXT: descriptive statistics
- PNG: histogram of n_tokens
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any

from bson import ObjectId

import sys; sys.path.append("..")
from mongo_client import articles_collection, facilities_collection, test_mongo_connection
from utils import combine_paragraphs


@dataclass
class ProjectBundle:
    project_id: str
    inst_canon: str | None
    iso2: str | None
    admin_group_key: str | None
    product_lv1: str | None
    article_ids: set[str]


def _as_object_id(value: Any) -> ObjectId | None:
    """Convert supported ID formats to ObjectId, else return None."""
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str):
        try:
            return ObjectId(value)
        except Exception:
            return None
    return None


def _extract_article_ids_from_events(events: Any) -> set[str]:
    """
    Extract unique article IDs from events only.

    Rule:
    - If number of events > 10, exclude events where event_type == "facility".
    """
    found: set[str] = set()
    if not isinstance(events, list):
        return found

    filtered_events = events
    if len(events) > 10:
        filtered_events = [
            e for e in events
            if not (isinstance(e, dict) and str(e.get("event_type", "")).lower() == "facility")
        ]

    for event in filtered_events:
        if not isinstance(event, dict):
            continue

        # Primary key used in your facilities docs.
        raw_values: list[Any] = [event.get("articleID")]

        for value in raw_values:
            if isinstance(value, list):
                for item in value:
                    oid = _as_object_id(item)
                    if oid is not None:
                        found.add(str(oid))
            else:
                oid = _as_object_id(value)
                if oid is not None:
                    found.add(str(oid))

    return found


def load_projects_and_article_ids(limit: int | None = None) -> dict[str, ProjectBundle]:
    """
    Load project metadata + linked article IDs from facilities.
    """
    project_map: dict[str, ProjectBundle] = {}

    cursor = facilities_collection.find({})
    if limit is not None:
        cursor = cursor.limit(limit)

    for doc in cursor:
        project_id = doc.get("project_id")
        if not project_id:
            continue

        if project_id not in project_map:
            project_map[project_id] = ProjectBundle(
                project_id=project_id,
                inst_canon=doc.get("inst_canon"),
                iso2=doc.get("iso2"),
                admin_group_key=doc.get("admin_group_key"),
                product_lv1=doc.get("product_lv1"),
                article_ids=set(),
            )

        events = doc.get("events", [])
        project_map[project_id].article_ids |= _extract_article_ids_from_events(events)

    return project_map


def load_article_texts(article_ids: set[str], batch_size: int = 500) -> dict[str, str]:
    """
    Fetch article full text for given ObjectId strings from articles collection.
    """
    id_list = [ObjectId(s) for s in article_ids]
    texts: dict[str, str] = {}

    for i in range(0, len(id_list), batch_size):
        batch = id_list[i : i + batch_size]
        cursor = articles_collection.find(
            {"_id": {"$in": batch}},
            {"title": 1, "paragraphs": 1},
        )
        for doc in cursor:
            text = combine_paragraphs(doc)
            if text:
                texts[str(doc["_id"])] = text

    return texts


def build_project_collection_text(project: ProjectBundle, article_text_by_id: dict[str, str]) -> tuple[str, int]:
    """
    Build the canonical collection text for one project.
    Returns (collection_text, n_articles_found).
    """
    lines = [
        f"project_id: {project.project_id}",
        f"inst_canon: {project.inst_canon or ''}",
        f"iso2: {project.iso2 or ''}",
        f"admin_group_key: {project.admin_group_key or ''}",
        f"product_lv1: {project.product_lv1 or ''}",
        "",
        "articles:",
    ]

    found = 0
    for aid in sorted(project.article_ids):
        text = article_text_by_id.get(aid)
        if not text:
            continue
        found += 1
        lines.append(f"--- article_id: {aid} ---")
        lines.append(text)
        lines.append("")

    return "\n".join(lines).strip(), found


def get_encoding(encoding_name: str | None = None, model_name: str | None = None):
    try:
        import tiktoken
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "tiktoken is required for token counting. Install it with: pip install tiktoken"
        ) from exc

    if model_name:
        try:
            return tiktoken.encoding_for_model(model_name)
        except Exception:
            pass
    return tiktoken.get_encoding(encoding_name or "cl100k_base")


def count_tokens(text: str, encoding) -> int:
    return len(encoding.encode(text))


def _percentile(values: list[int], q: float) -> float:
    """Compute percentile with linear interpolation (q in [0, 100])."""
    if not values:
        return 0.0
    xs = sorted(float(v) for v in values)
    if len(xs) == 1:
        return xs[0]
    pos = (q / 100.0) * (len(xs) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def summarize_distribution(values: list[int]) -> dict[str, float]:
    if not values:
        return {
            "count": 0.0,
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "p05": 0.0,
            "p25": 0.0,
            "p50": 0.0,
            "p75": 0.0,
            "p95": 0.0,
            "p99": 0.0,
        }

    return {
        "count": float(len(values)),
        "min": float(min(values)),
        "max": float(max(values)),
        "mean": float(mean(values)),
        "median": float(median(values)),
        "std": float(pstdev(values)),
        "p05": _percentile(values, 5),
        "p25": _percentile(values, 25),
        "p50": _percentile(values, 50),
        "p75": _percentile(values, 75),
        "p95": _percentile(values, 95),
        "p99": _percentile(values, 99),
    }


def write_stats_report(path: Path, stats: dict[str, float], n_zero_articles: int) -> None:
    lines = [
        "Project summary token distribution report",
        "",
        f"count:   {int(stats['count'])}",
        f"min:     {stats['min']:.0f}",
        f"max:     {stats['max']:.0f}",
        f"mean:    {stats['mean']:.2f}",
        f"median:  {stats['median']:.2f}",
        f"std:     {stats['std']:.2f}",
        f"p05:     {stats['p05']:.2f}",
        f"p25:     {stats['p25']:.2f}",
        f"p50:     {stats['p50']:.2f}",
        f"p75:     {stats['p75']:.2f}",
        f"p95:     {stats['p95']:.2f}",
        f"p99:     {stats['p99']:.2f}",
        "",
        f"projects_with_zero_found_articles: {n_zero_articles}",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def plot_histogram(path: Path, values: list[int]) -> None:
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "matplotlib is required to render the histogram. "
            "Install it with: pip install matplotlib"
        ) from exc

    plt.figure(figsize=(10, 6))
    plt.hist(values, bins="auto", edgecolor="black")
    plt.title("Distribution of n_tokens across project collections")
    plt.xlabel("n_tokens")
    plt.ylabel("Number of projects")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def run(limit: int | None, output_dir: Path, encoding_name: str | None, model_name: str | None) -> None:
    test_mongo_connection()
    output_dir.mkdir(parents=True, exist_ok=True)

    project_map = load_projects_and_article_ids(limit=limit)
    if not project_map:
        raise RuntimeError("No projects found in facilities.")

    all_article_ids = set()
    for project in project_map.values():
        all_article_ids |= project.article_ids

    article_text_by_id = load_article_texts(all_article_ids)
    encoding = get_encoding(encoding_name=encoding_name, model_name=model_name)

    rows: list[dict[str, Any]] = []
    token_values: list[int] = []
    n_zero_articles = 0

    for project in project_map.values():
        collection_text, n_found = build_project_collection_text(project, article_text_by_id)
        n_tokens = count_tokens(collection_text, encoding)
        n_chars = len(collection_text)
        if n_found == 0:
            n_zero_articles += 1

        rows.append(
            {
                "project_id": project.project_id,
                "inst_canon": project.inst_canon,
                "iso2": project.iso2,
                "admin_group_key": project.admin_group_key,
                "product_lv1": project.product_lv1,
                "n_article_ids_linked": len(project.article_ids),
                "n_articles_found": n_found,
                "n_chars": n_chars,
                "n_tokens": n_tokens,
            }
        )
        token_values.append(n_tokens)

    rows_sorted = sorted(rows, key=lambda r: r["n_tokens"], reverse=True)
    stats = summarize_distribution(token_values)

    csv_path = output_dir / "project_summary_n_tokens.csv"
    stats_path = output_dir / "project_summary_token_stats.txt"
    hist_path = output_dir / "project_summary_token_histogram.png"

    if rows_sorted:
        fieldnames = list(rows_sorted[0].keys())
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows_sorted)
    else:
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["project_id", "n_tokens"])

    write_stats_report(stats_path, stats, n_zero_articles=n_zero_articles)
    plot_histogram(hist_path, token_values)

    print(f"Projects processed: {len(rows_sorted)}")
    print(f"Total linked article IDs: {sum(r['n_article_ids_linked'] for r in rows_sorted)}")
    print(f"Articles found in articles collection: {sum(r['n_articles_found'] for r in rows_sorted)}")
    print(f"CSV: {csv_path}")
    print(f"Stats: {stats_path}")
    print(f"Histogram: {hist_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute token distribution over project summary collections (MongoDB only)."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="storage/output",
        help="Directory for CSV, stats report, and histogram.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on number of facilities docs read.",
    )
    parser.add_argument(
        "--encoding",
        type=str,
        default="cl100k_base",
        help="tiktoken encoding name (ignored if --model is provided and recognized).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Optional model name to resolve tokenizer via tiktoken.encoding_for_model.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(
        limit=args.limit,
        output_dir=Path(args.output_dir),
        encoding_name=args.encoding,
        model_name=args.model,
    )
