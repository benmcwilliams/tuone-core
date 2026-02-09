import sys; sys.path.append("../..")
from mongo_client import articles_collection
from scrape.keywords import SUBSIDY_KEYWORDS
from datetime import datetime
import re

cutoff_date = datetime(2019, 1, 1)

def build_text_blob(doc: dict) -> str:
    title = (doc.get("title") or "").strip()

    paras = doc.get("paragraphs") or []
    body = []

    if isinstance(paras, list) and paras and isinstance(paras[0], dict):
        body = [str(v) for v in paras[0].values() if v]

    return (title + " " + " ".join(body)).lower()

SUBSIDY_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in SUBSIDY_KEYWORDS) + r")\b",
    re.IGNORECASE
)

def has_subsidy(text_lc: str) -> bool:
    return bool(SUBSIDY_REGEX.search(text_lc))


def main(dry_run: bool = False):
    query = {"meta.category": {"$in": ["user", "pvmagazine", "pvtech"]},
        "meta.date": {"$gt": cutoff_date},
    }
    cursor = articles_collection.find(
        query,
        projection={"title": 1, "paragraphs": 1, "meta.subsidy": 1}
    )

    processed = updated = 0

    for doc in cursor:
        processed += 1

        text_lc = build_text_blob(doc)
        subsidy_flag = has_subsidy(text_lc)

        current = (doc.get("meta") or {}).get("subsidy")
        if current is not None and current == subsidy_flag:
            continue

        updated += 1

        if dry_run:
            print(f"[DRY RUN] {doc['_id']} → subsidy={subsidy_flag}")
        else:
            articles_collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"meta.subsidy": subsidy_flag}}
            )

    print(f"Done. processed={processed}, updated={updated}")


if __name__ == "__main__":
    main(dry_run=False)   # set True to preview