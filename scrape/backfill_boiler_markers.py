import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from pymongo import UpdateOne

sys.path.append(str(Path(__file__).resolve().parents[1]))
from mongo_client import articles_collection, test_mongo_connection
from boiler_markers import BOILER_STRINGS
from scrap_function.utility import should_skip_paragraph


def _paragraph_key_sort_key(key: str) -> tuple[int, str]:
    if key.startswith("p") and key[1:].isdigit():
        return (0, f"{int(key[1:]):08d}")
    return (1, key)


def _extract_paragraph_texts(paragraphs: Any) -> tuple[list[str], bool]:
    if isinstance(paragraphs, dict):
        paragraph_objects = [paragraphs]
    elif isinstance(paragraphs, list) and all(isinstance(item, dict) for item in paragraphs):
        paragraph_objects = paragraphs
    else:
        return ([], False)

    lines: list[str] = []
    for para_obj in paragraph_objects:
        for key in sorted(para_obj.keys(), key=_paragraph_key_sort_key):
            value = para_obj.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                lines.append(text)
    return (lines, True)


def _clean_lines(lines: Iterable[str]) -> list[str]:
    cleaned: list[str] = []
    for txt in lines:
        if not txt or txt in BOILER_STRINGS or should_skip_paragraph(txt):
            continue
        cleaned.append(txt)
    return cleaned


def _clean_lines_with_removed(lines: Iterable[str]) -> tuple[list[str], list[str]]:
    """Return (cleaned_lines, removed_lines) for reporting."""
    cleaned: list[str] = []
    removed: list[str] = []
    for txt in lines:
        if not txt or txt in BOILER_STRINGS or should_skip_paragraph(txt):
            removed.append(txt or "(empty)")
        else:
            cleaned.append(txt)
    return cleaned, removed


def _to_paragraph_payload(lines: list[str]) -> list[dict[str, str]]:
    return [{f"p{idx + 1}": txt for idx, txt in enumerate(lines)}]


def _build_update_operations(
    *,
    category: str | None,
    limit: int | None,
    dry_run: bool,
    sample_size: int,
) -> tuple[list[UpdateOne], dict[str, int], list[str], list[tuple[str, list[str]]]]:
    query: dict[str, Any] = {
        "paragraphs": {"$exists": True, "$ne": None},
    }
    if category:
        query["meta.category"] = category

    projection = {
        "_id": 1,
        "paragraphs": 1,
    }

    cursor = articles_collection.find(query, projection=projection)
    if limit:
        cursor = cursor.limit(limit)

    counters = {
        "scanned": 0,
        "changed": 0,
        "unchanged": 0,
        "skipped_invalid": 0,
        "paragraphs_removed": 0,
    }
    sample_lines: list[str] = []
    sample_removed: list[tuple[str, list[str]]] = []  # (doc_id_str, removed_texts)
    ops: list[UpdateOne] = []

    for doc in cursor:
        counters["scanned"] += 1
        original = doc.get("paragraphs")
        original_lines, valid = _extract_paragraph_texts(original)

        if not valid:
            counters["skipped_invalid"] += 1
            continue

        cleaned_lines, removed_lines = _clean_lines_with_removed(original_lines)
        removed_count = len(removed_lines)
        counters["paragraphs_removed"] += removed_count

        cleaned_payload = _to_paragraph_payload(cleaned_lines)
        if cleaned_payload == original:
            counters["unchanged"] += 1
            continue

        counters["changed"] += 1
        if len(sample_lines) < sample_size:
            sample_lines.append(
                f"{doc['_id']} | paragraphs {len(original_lines)} -> {len(cleaned_lines)}"
            )
            if removed_lines:
                sample_removed.append((str(doc["_id"]), removed_lines))

        if not dry_run:
            ops.append(
                UpdateOne(
                    {"_id": doc["_id"]},
                    {
                        "$set": {
                            "paragraphs": cleaned_payload,
                            "meta.boiler_markers_backfilled_at": datetime.now(timezone.utc),
                        }
                    },
                )
            )

    return ops, counters, sample_lines, sample_removed


def backfill_boiler_markers(
    *,
    dry_run: bool = True,
    category: str | None = None,
    limit: int | None = None,
    batch_size: int = 500,
    sample_size: int = 10,
) -> None:
    test_mongo_connection()

    ops, counters, sample_lines, sample_removed = _build_update_operations(
        category=category,
        limit=limit,
        dry_run=dry_run,
        sample_size=sample_size,
    )

    print(
        f"Run mode: {'DRY RUN' if dry_run else 'WRITE'} | "
        f"category={category or 'all'} | limit={limit or 'none'} | batch_size={batch_size}"
    )
    print(
        "Scanned={scanned}, Changed={changed}, Unchanged={unchanged}, "
        "SkippedInvalid={skipped_invalid}, ParagraphsRemoved={paragraphs_removed}".format(**counters)
    )

    if sample_lines:
        print("\nSample changed docs:")
        for line in sample_lines:
            print(f"- {line}")
        if sample_removed:
            print("\nText that would be removed (sample):")
            for doc_id, removed_texts in sample_removed:
                print(f"\n  [{doc_id}]")
                for txt in removed_texts:
                    snippet = txt if len(txt) <= 120 else txt[:117] + "..."
                    print(f"    - {snippet!r}")

    if dry_run:
        print("\nDry run complete. No database writes performed.")
        return

    if not ops:
        print("\nNo updates to apply.")
        return

    total_matched = 0
    total_modified = 0
    batches = 0

    for i in range(0, len(ops), batch_size):
        batch = ops[i : i + batch_size]
        result = articles_collection.bulk_write(batch, ordered=False)
        batches += 1
        total_matched += result.matched_count
        total_modified += result.modified_count
        print(
            f"Batch {batches}: submitted={len(batch)}, "
            f"matched={result.matched_count}, modified={result.modified_count}"
        )

    print(
        f"\nWrite complete. batches={batches}, "
        f"total_matched={total_matched}, total_modified={total_modified}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill boiler marker paragraph cleanup for already-scraped articles."
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Preview changes without writing. Default: True. Use --no-dry-run to write.",
    )
    parser.add_argument(
        "--category",
        default=None,
        help="Optional meta.category filter (e.g. electrive).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional max number of articles to scan.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Bulk write batch size when not in dry-run mode.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=10,
        help="Number of changed doc samples to print.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    backfill_boiler_markers(
        dry_run=args.dry_run,
        category=args.category,
        limit=args.limit,
        batch_size=args.batch_size,
        sample_size=args.sample_size,
    )
