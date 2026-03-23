#!/usr/bin/env python3
"""
Print how many articles have been llm_processed and the breakdown by run_id and by meta.category.
Uses the articles collection from mongo_client (MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION_NAME).
"""
import sys
from pathlib import Path

# Project root (parent of database-operations)
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from mongo_client import articles_collection, test_mongo_connection


def main():
    test_mongo_connection()

    total = articles_collection.count_documents({})
    llm_processed_count = articles_collection.count_documents({"llm_processed": {"$exists": True, "$ne": None}})
    not_processed = total - llm_processed_count

    pipeline_run = [
        {"$match": {"llm_processed": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$llm_processed.run_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    by_run = list(articles_collection.aggregate(pipeline_run))

    pipeline_category = [
        {
            "$group": {
                "_id": "$meta.category",
                "total": {"$sum": 1},
                "llm_processed": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$ne": ["$llm_processed", None]},
                                {"$ne": [{"$type": "$llm_processed"}, "missing"]},
                            ]},
                            1,
                            0,
                        ]
                    }
                },
                "run_v2_0": {
                    "$sum": {"$cond": [{"$eq": ["$llm_processed.run_id", "v2.0"]}, 1, 0]}
                },
                "run_v1_1": {
                    "$sum": {"$cond": [{"$eq": ["$llm_processed.run_id", "v1.1"]}, 1, 0]}
                },
            }
        },
        {"$addFields": {"not_processed": {"$subtract": ["$total", "$llm_processed"]}}},
        {"$sort": {"total": -1}},
    ]
    by_category = list(articles_collection.aggregate(pipeline_category))

    run_counts = {row["_id"]: row["count"] for row in by_run}
    count_v2_0 = run_counts.get("v2.0", 0)
    count_v1_1 = run_counts.get("v1.1", 0)

    print("=== Articles LLM processed stats ===\n")
    print(f"Total articles:        {total:,}")
    print(f"LLM processed:         {llm_processed_count:,}")
    print(f"Not LLM processed:     {not_processed:,}")
    print()
    print("By run_id:")
    print("-" * 30)
    for row in by_run:
        run_id = row["_id"] if row["_id"] is not None else "(null)"
        print(f"  {run_id:<20} {row['count']:,}")
    print("-" * 30)
    print(f"  {'(total processed)':<20} {llm_processed_count:,}")
    print()
    pct_v2_0_total = (100 * count_v2_0 / llm_processed_count) if llm_processed_count else 0
    pct_v1_1_total = (100 * count_v1_1 / llm_processed_count) if llm_processed_count else 0

    print("By meta.category:")
    print("-" * 95)
    print(f"  {'category':<25} {'total':>10} {'processed':>10} {'not_proc':>10}  {'%':>6}  {'v2.0%':>7}  {'v1.1%':>7}")
    print("-" * 95)
    for row in by_category:
        cat = row["_id"] if row["_id"] is not None else "(null)"
        pct = (100 * row["llm_processed"] / row["total"]) if row["total"] else 0
        pct_v2 = (100 * row["run_v2_0"] / row["llm_processed"]) if row["llm_processed"] else 0
        pct_v1 = (100 * row["run_v1_1"] / row["llm_processed"]) if row["llm_processed"] else 0
        print(
            f"  {str(cat):<25} {row['total']:>10,} {row['llm_processed']:>10,} {row['not_processed']:>10,}  {pct:>5.1f}%  {pct_v2:>6.1f}%  {pct_v1:>6.1f}%"
        )
    print("-" * 95)
    print(f"  {'(total)':<25} {total:>10,} {llm_processed_count:>10,} {not_processed:>10,}  {(100 * llm_processed_count / total) if total else 0:>5.1f}%  {pct_v2_0_total:>6.1f}%  {pct_v1_1_total:>6.1f}%")


if __name__ == "__main__":
    main()
