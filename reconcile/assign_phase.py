# assign_phases.py
# -----------------------------------------------------------------------------
# PURPOSE
#   Assign a phase number (phase_num) to every event inside each project
#   document in MongoDB, using a simple, idempotent v1 rule set.
# -----------------------------------------------------------------------------

import sys; sys.path.append("..")
import logging
from copy import deepcopy
from pymongo import UpdateOne
from mongo_client import facilities_collection

logger = logging.getLogger(__name__)

# ------------------- CONFIGURATION -------------------
DRY_RUN = True         # True = preview only, False = actually write to DB
LIMIT = 50             # None = all docs, or set e.g. 50 for testing
QUERY = {"iso2": "GR"} # Mongo filter, e.g. {"iso2": "DE"} or {} for all
# -----------------------------------------------------

# check whether user has set phase_num == "ignore"
def _is_ignored(ev: dict) -> bool:
    v = ev.get("phase_num")
    return isinstance(v, str) and v.strip().lower() == "ignore"

def _phase_num_is_set(ev: dict) -> bool:
    if _is_ignored(ev):
        return True
    return ev.get("phase_num") is not None

def _has_greenfield(events) -> bool:
    return any((isinstance(ev, dict) and not _is_ignored(ev) and ev.get("phase") == "greenfield") for ev in (events or []))

def _has_expansion(events) -> bool:
    return any((isinstance(ev, dict) and not _is_ignored(ev) and ev.get("phase") == "expansion") for ev in (events or []))


def _assign_phase_nums_v1(events: list) -> tuple[list, int]:
    """Apply v1 rules to events. Returns (updated_events, num_changes)."""
    if not isinstance(events, list) or not events:
        return events, 0

    updated = deepcopy(events)
    changes = 0

    has_green = _has_greenfield(updated)
    has_expand = _has_expansion(updated)

    # Rule 1: greenfield -> 1
    for ev in updated:
        if ev.get("phase") == "greenfield" and not _phase_num_is_set(ev):
            ev["phase_num"] = 1
            changes += 1

    # Rule 2: expansion-only -> 1
    if has_expand and not has_green:
        for ev in updated:
            if ev.get("phase") == "expansion" and not _phase_num_is_set(ev):
                ev["phase_num"] = 1
                changes += 1

    # Rule 3: greenfield present -> expansion -> 2
    if has_green:
        for ev in updated:
            if ev.get("phase") == "expansion" and not _phase_num_is_set(ev):
                ev["phase_num"] = 2
                changes += 1

    # Rule 4: no expansions -> all remaining -> 1
    if not has_expand:
        for ev in updated:
            if not _phase_num_is_set(ev):
                ev["phase_num"] = 1
                changes += 1

    return updated, changes


def assign_phase_num(dry_run: bool = True, limit: int | None = None, query: dict | None = None):

    cursor = facilities_collection.find(query or {}, projection={"events": 1, "project_id": 1})
    if limit is not None and limit > 0:
        cursor = cursor.limit(limit)

    bulk_ops = []
    total_docs = 0
    total_ev_changes = 0
    changed_docs = 0

    for doc in cursor:
        total_docs += 1
        events = doc.get("events", [])
        updated_events, changes = _assign_phase_nums_v1(events)

        if changes > 0:
            changed_docs += 1
            total_ev_changes += changes
            logger.info(f"Project {doc.get('project_id')} | events updated: {changes}")
            if not dry_run:
                bulk_ops.append(UpdateOne({"_id": doc["_id"]}, {"$set": {"events": updated_events}}))

        # Flush occasionally
        if not dry_run and len(bulk_ops) >= 500:
            res = facilities_collection.bulk_write(bulk_ops, ordered=False)
            logger.info(f"Bulk write: matched {res.matched_count}, modified {res.modified_count}")
            bulk_ops = []

    if not dry_run and bulk_ops:
        res = facilities_collection.bulk_write(bulk_ops, ordered=False)
        logger.info(f"Bulk write: matched {res.matched_count}, modified {res.modified_count}")

    logger.info(
        f"Finished. Docs scanned: {total_docs} | Docs changed: {changed_docs} | "
        f"Event updates applied: {total_ev_changes} | Mode: {'DRY-RUN' if dry_run else 'COMMIT'}"
    )


if __name__ == "__main__":
    logger.info(
        f"Starting assign_phases.py | Mode: {'DRY-RUN' if DRY_RUN else 'COMMIT'} | "
        f"Limit: {LIMIT or 'none'} | Query: {QUERY or '{}'}"
    )
    process_documents(dry_run=DRY_RUN, limit=LIMIT, query=QUERY)