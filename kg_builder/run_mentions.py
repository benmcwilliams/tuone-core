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

# --- Config: edit these in the file ---
dry_run = False
limit = None  # None = no limit, or set e.g. 10
article_id = None  # None = all matching articles, or set a single MongoDB ObjectId string
categories = ["electrive"]  # same as main.py: only these meta.category values
cutoff_date = datetime(2021, 1, 1)  # only articles with meta.date > this
offset_articles = 0  # skip this many articles (for resuming)


def main() -> None:
    test_mongo_connection()
    print(f"Config: dry_run={dry_run}, limit={limit}, article_id={article_id}, cutoff_date={cutoff_date}, offset={offset_articles}")

    query = {
        "nodes": {"$exists": True, "$ne": []},
        "paragraphs": {"$exists": True, "$ne": []},
        "meta.category": {"$in": categories},
        "meta.date": {"$gt": cutoff_date},
    }
    if article_id:
        from bson import ObjectId
        try:
            oid = ObjectId(article_id)
        except Exception:
            print(f"Invalid article_id: {article_id}")
            return
        query["_id"] = oid

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
    cursor = articles_collection.find(query, projection).sort("_id", 1).skip(offset_articles)
    if limit is not None:
        cursor = cursor.limit(limit)
    articles = list(cursor)

    print(f"Found {len(articles)} article(s) with nodes and paragraphs.")
    to_run = [a for a in articles if should_run_mentions(a)]
    print(f"Will run mentions for {len(to_run)} article(s) (timestamp or missing mentions_ts).")

    for article in articles:
        if not should_run_mentions(article):
            continue
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
            print(f"  Updated: {len(mentions)} mentions, mentions_ts={now}")
        except Exception as e:
            import traceback
            print(f"  Error: {type(e).__name__}: {e}")
            traceback.print_exc()
        finally:
            for h in list(logger.handlers):
                h.close()
                logger.removeHandler(h)


if __name__ == "__main__":
    main()
