import sys; sys.path.append("..")
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from mongo_client import facilities_collection
from mongo_client_clone import get_target_client


TARGET_DB_NAME = "opensourcedev"
TARGET_COLLECTION_NAME = "inst_canon"
BACKUP_EXCEL_PATH = Path(__file__).resolve().parent / "storage" / "input" / "inst_canon.xlsx"


def _clean_inst_canon(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return None


def _export_inst_canon_to_excel(collection) -> None:
    """Export current inst_canon collection to Excel as a backup before any changes."""
    cursor = collection.find({}, {"_id": 0, "inst_canon": 1, "HQ_ISO2": 1, "inst_manual": 1})
    rows = list(cursor)
    df = pd.DataFrame(rows)
    BACKUP_EXCEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(BACKUP_EXCEL_PATH, index=False, engine="openpyxl")
    logging.info("inst_canon backup written: %s (%d rows)", BACKUP_EXCEL_PATH, len(df))


def _current_inst_canon_from_facilities() -> set[str]:
    raw_values = facilities_collection.distinct("inst_canon")
    cleaned = {_clean_inst_canon(v) for v in raw_values}
    return {v for v in cleaned if v}


def sync_inst_canon_to_opensourcedev() -> None:
    current_inst_canon = _current_inst_canon_from_facilities()
    if not current_inst_canon:
        logging.warning(
            "Skipping inst_canon sync: no inst_canon values found in facilities_develop."
        )
        return

    try:
        target_client = get_target_client()
    except Exception as exc:
        logging.warning(
            "Skipping inst_canon sync: opensource target cluster not configured (%s).",
            exc,
        )
        return

    target_coll = target_client[TARGET_DB_NAME][TARGET_COLLECTION_NAME]

    _export_inst_canon_to_excel(target_coll)

    existing_raw = target_coll.distinct("inst_canon")
    existing_inst_canon = {v for v in (_clean_inst_canon(x) for x in existing_raw) if v}

    to_add = sorted(current_inst_canon - existing_inst_canon)
    stale = sorted(existing_inst_canon - current_inst_canon)

    if to_add:
        target_coll.insert_many(
            [{"inst_canon": name, "HQ_ISO2": None, "inst_manual": None} for name in to_add],
            ordered=False,
        )

    removed = 0
    if stale:
        result = target_coll.delete_many({"inst_canon": {"$in": stale}})
        removed = result.deleted_count

    logging.info(
        "inst_canon sync complete: facilities_unique=%d, added=%d, removed=%d, final_target=%d",
        len(current_inst_canon),
        len(to_add),
        removed,
        target_coll.count_documents({}),
    )


if __name__ == "__main__":
    sync_inst_canon_to_opensourcedev()
