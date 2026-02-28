"""
Standalone script to compute and update node mentions for articles.
Run from project root: python kg_builder/run_mentions.py
"""
import sys
from pathlib import Path

# Ensure project root and kg_builder are on path
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_script_dir))

from dotenv import load_dotenv
load_dotenv(_project_root / ".env")

from mongo_client import articles_collection, test_mongo_connection
from src.process_articles import setup_logger
from src.mentions import should_run_mentions, run_mentions_extraction
from datetime import datetime, timezone

# --- Config: edit these in the file (used when run as __main__) ---
dry_run = False
limit = None  # None = no limit, or set e.g. 10
article_id = None  # None = all matching articles, or set a single MongoDB ObjectId string
categories = None  # None or [] = all categories; or e.g. ["enrichment"]
cutoff_date = datetime(2000, 1, 1)  # only articles with meta.date > this
offset_articles = 0  # skip this many articles (for resuming)
batch_size = 500  # fetch and process in batches (ignored if limit is set and smaller)


# MongoDB filter: only articles that need a mentions update (no mentions_ts, or llm/validation newer)
NEEDS_UPDATE_OR = [
    {"mentions_ts": {"$exists": False}},
    {"mentions_ts": None},
    {"mentions_ts": ""},
    {"$expr": {"$gt": ["$llm_processed.ts", "$mentions_ts"]}},
    {
        "$expr": {
            "$and": [
                {"$eq": [{"$type": "$validation"}, "string"]},
                {"$gt": ["$validation", "$mentions_ts"]},
            ]
        }
    },
]


def run_mentions_pipeline(
    *,
    dry_run: bool = False,
    limit: int | None = None,
    article_id: str | None = None,
    categories: list[str] | None = None,
    cutoff_date: datetime | None = None,
    offset_articles: int = 0,
    batch_size: int = 500,
) -> None:
    """
    Compute and update node mentions for articles that need it.
    Only fetches articles that need an update (no mentions_ts or llm_processed/validation after mentions_ts).
    """
    test_mongo_connection()
    cutoff_date = cutoff_date or datetime(2000, 1, 1)
    print(
        f"Config: dry_run={dry_run}, limit={limit}, article_id={article_id}, "
        f"cutoff_date={cutoff_date}, offset={offset_articles}, batch_size={batch_size}"
    )

    query = {
        "nodes": {"$exists": True, "$ne": []},
        "paragraphs": {"$exists": True, "$ne": []},
        "meta.date": {"$gt": cutoff_date},
        "$or": NEEDS_UPDATE_OR,
    }
    if categories:
        query["meta.category"] = {"$in": categories}
    if article_id:
        from bson import ObjectId
        try:
            query["_id"] = ObjectId(article_id)
        except Exception:
            print(f"Invalid article_id: {article_id}")
            return

    projection = {
        "_id": 1,
        "meta": 1,
        "paragraphs": 1,
        "nodes": 1,
        "mentions_ts": 1,
        "llm_processed": 1,
        "validation": 1,
        "title": 1,
    }

    total_to_process = articles_collection.count_documents(query)
    print(f"Found {total_to_process} article(s) that need mentions update.")

    processed = 0
    updated = 0
    offset = offset_articles

    while True:
        batch_limit = batch_size if limit is None else min(batch_size, limit - processed)
        if batch_limit <= 0:
            break
        cursor = (
            articles_collection.find(query, projection)
            .sort("_id", 1)
            .skip(offset)
            .limit(batch_limit)
        )
        articles = list(cursor)
        if not articles:
            break

        for article in articles:
            if limit is not None and processed >= limit:
                break
            if not should_run_mentions(article):
                continue
            processed += 1
            aid = str(article["_id"])
            print(f"Processing article {aid}: {article.get('title', '')[:60]}...")
            logger = setup_logger(aid, log_dir="logs/mentions")
            try:
                mentions = run_mentions_extraction(
                    article["paragraphs"],
                    article["nodes"],
                    logger,
                )
                if dry_run:
                    print(f"  [dry-run] would set {len(mentions)} mentions")
                    continue
                now = datetime.now(timezone.utc).isoformat()
                articles_collection.update_one(
                    {"_id": article["_id"]},
                    {"$set": {"mentions": mentions, "mentions_ts": now}},
                )
                updated += 1
                print(f"  Updated: {len(mentions)} mentions, mentions_ts={now}")
            except Exception as e:
                import traceback
                print(f"  Error: {type(e).__name__}: {e}")
                traceback.print_exc()
            finally:
                for h in list(logger.handlers):
                    h.close()
                    logger.removeHandler(h)

        offset += len(articles)
        if limit is not None and processed >= limit:
            break
        if len(articles) < batch_limit:
            break
        print(f"Batch: {offset} / {total_to_process} scanned.")

    print(f"Done. Processed {processed} article(s), updated {updated}.")


def main() -> None:
    run_mentions_pipeline(
        dry_run=dry_run,
        limit=limit,
        article_id=article_id,
        categories=categories,
        cutoff_date=cutoff_date,
        offset_articles=offset_articles,
        batch_size=batch_size,
    )


if __name__ == "__main__":
    main()
