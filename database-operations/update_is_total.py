import sys; sys.path.append("..")
import os
from pymongo import MongoClient
from pymongo.client_session import ClientSession

# ---------- Config ----------

from mongo_client import db, mongo_client, test_mongo_connection
test_mongo_connection()
col = db["articles_clone"]

# Safety: start with dry-run; set to True to apply
APPLY_CHANGES = False

base_match = {"nodes.type": "investment"}  # limit scope to docs that have investment nodes

def count_affected(collection):
    """Return: (docs_affected, total_investment_nodes_missing_is_total)"""
    pipeline = [
        {"$match": base_match},
        {"$project": {
            "missing_investments": {
                "$filter": {
                    "input": "$nodes",
                    "as": "n",
                    "cond": {
                        "$and": [
                            {"$eq": ["$$n.type", "investment"]},
                            {"$eq": [{"$ifNull": ["$$n.is_total", None]}, None]}
                        ]
                    }
                }
            }
        }},
        {"$project": {
            "cnt": {"$size": "$missing_investments"}
        }},
        {"$group": {
            "_id": None,
            "docs_affected": {"$sum": {"$cond": [{"$gt": ["$cnt", 0]}, 1, 0]}},
            "nodes_missing": {"$sum": "$cnt"}
        }}
    ]
    out = list(collection.aggregate(pipeline, allowDiskUse=True))
    if not out:
        return 0, 0
    return out[0]["docs_affected"], out[0]["nodes_missing"]

def apply_update(collection, session: ClientSession | None = None):
    """
    Set is_total=true for investment nodes where is_total is missing/null.
    Pipeline update modifies the nodes array in-place, touching only targets.
    """
    update_pipeline = [
        {"$set": {
            "nodes": {
                "$map": {
                    "input": "$nodes",
                    "as": "n",
                    "in": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$eq": ["$$n.type", "investment"]},
                                    {"$eq": [{"$ifNull": ["$$n.is_total", None]}, None]}
                                ]
                            },
                            {"$mergeObjects": ["$$n", {"is_total": True}]},
                            "$$n"
                        ]
                    }
                }
            }
        }}
    ]
    return col.update_many(base_match, update_pipeline, session=session)

if __name__ == "__main__":
    total_docs = col.count_documents({})
    print(f"Total docs: {total_docs}")

    docs_aff, nodes_aff = count_affected(col)
    print(f"[DRY-RUN] Docs with missing/null is_total on investment nodes: {docs_aff}")
    print(f"[DRY-RUN] Investment nodes missing/null is_total: {nodes_aff}")

    if not APPLY_CHANGES:
        print("[DRY-RUN] No changes applied. Set APPLY_CHANGES=True to perform the update.")
    else:
        # Try a transaction if supported; else fall back gracefully
        try:
            with mongo_client.start_session() as session:
                def txn(sess):
                    res = apply_update(col, session=sess)
                    print(f"[APPLY] Matched: {res.matched_count}, Modified: {res.modified_count}")

                try:
                    session.with_transaction(txn)
                except Exception:
                    # Fallback: run outside transaction (e.g., standalone)
                    res = apply_update(col, session=None)
                    print(f"[APPLY-no-tx] Matched: {res.matched_count}, Modified: {res.modified_count}")
        except Exception:
            # Sessions not supported -> plain update
            res = apply_update(col, session=None)
            print(f"[APPLY-basic] Matched: {res.matched_count}, Modified: {res.modified_count}")

        # Verify
        docs_aff_after, nodes_aff_after = count_affected(col)
        print(f"[VERIFY] Remaining docs needing update: {docs_aff_after}")
        print(f"[VERIFY] Remaining investment nodes needing update: {nodes_aff_after}")