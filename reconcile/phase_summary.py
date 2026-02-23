# phase_summary.py
# -----------------------------------------------------------------------------
# PURPOSE
#   Build phase summaries for each phase_num in each facility document in MongoDB.
#   Summarise capacity and investment events by phase_num.
#   Calculate the strongest status (lowest STATUS_RANK, then most recent date).
#   Calculate the cumulative capacity and investment.
#   Calculate the earliest milestone dates (announce, under construction, operational).
# -----------------------------------------------------------------------------
#from cmath import phase
import logging
import re
import sys; sys.path.append("..")
from pymongo import UpdateOne
from datetime import datetime
import pandas as pd
from mongo_client import facilities_collection, articles_collection
from bson import ObjectId
from src.attach_events_helpers import normalize_pl2, normalize_pl3

## main logic should be updated to read from phases (or drop main...)

STATUS_NORMALIZE = {
    "ongoing": "under construction",
    "completed": "operational",
}
STATUS_ORDER = ["cancelled", "paused", "operational", "under construction", "announced", "unclear"]
STATUS_RANK = {status: i for i, status in enumerate(STATUS_ORDER)}

PAUSELIKE = {"cancelled", "paused"}  # facility events can only vote for pauses or cancellations
INV_PAUSELIKE = PAUSELIKE | {"under construction", "announced"}

ARTICLE_ID_FIELD = "_id"
ATTACH_COMMENTS = False

# --------- helpers -------------

def parse_date(date_str):
    """Parse date string to pandas Timestamp, returns NaT on error."""
    return pd.to_datetime(date_str, errors="coerce")

def phase_is_ignored(ev: dict) -> bool:
    v = ev.get("phase_num")
    return isinstance(v, str) and v.strip().lower() == "ignore"

def parse_tract_stage(phase_num: int | str | float | None) -> tuple[str | None, int | None]:
    """
    Parse phase_num into (tract, stage) tuple.
    
    - "A.1", "B.2" → ("A", 1), ("B", 2)  (tract.stage format)
    - 1, "1" → (None, 1)  (legacy integer format, no tract)
    - None, "ignore" → (None, None)
    
    Returns:
        (tract: str | None, stage: int | None)
    """
    if phase_num is None:
        return (None, None)
    
    if isinstance(phase_num, int):
        return (None, phase_num)
    
    if isinstance(phase_num, float):
        if phase_num.is_integer():
            return (None, int(phase_num))
        # Non-integer float like 1.1 - treat as legacy decimal, no tract
        return (None, None)
    
    if isinstance(phase_num, str):
        s = phase_num.strip()
        if s.lower() == "ignore":
            return (None, None)
        
        # Match tract.stage format: letters followed by dot and digits (e.g., "A.1", "B.2")
        match = re.fullmatch(r"([A-Za-z]+)\.(\d+)", s)
        if match:
            tract = match.group(1).upper()  # normalize to uppercase
            stage = int(match.group(2))
            return (tract, stage)
        
        # Legacy integer format
        if re.fullmatch(r"\d+", s):
            return (None, int(s))
    
    return (None, None)

def phase_num_tract_stage(ev: dict) -> str | None:
    """
    Return normalized tract.stage phase_num (e.g., 'A.1') if present, else None.
    Only returns values that match the tract.stage format (letters.stage).
    """
    v = ev.get("phase_num")
    tract, stage = parse_tract_stage(v)
    if tract is not None and stage is not None:
        return f"{tract}.{stage}"
    return None

def phase_num_int(ev: dict) -> int | None:
    ''' 
    Safely evaluate all phase numbers as integers, even if they are read in as strings. 
    '''
    v = ev.get("phase_num")
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s == "ignore":
            return None
        if re.fullmatch(r"\d+", s):  # accepts "2", " 2 ", "02"
            return int(s)
    return None

def _is_relevant_event(c: dict, phase_num: int | str | None) -> bool:
    """
    Returns a boolean for whether an event should be included or not.
    Basic filter: valid status, not ignored, has date, and matches phase if specified.
    """
    if c.get("status") not in STATUS_ORDER:
        return False
    if phase_is_ignored(c):
        return False
    if not c.get("date"):
        return False

    # Phase filter
    if phase_num is None:
        return True

    # Parse both the target phase_num and the event's phase_num
    target_tract, target_stage = parse_tract_stage(phase_num)
    ev_tract, ev_stage = parse_tract_stage(c.get("phase_num"))

    # Both must have valid stages to match
    if target_stage is None or ev_stage is None:
        return False

    # Match: same tract (both None for legacy, or same string) and same stage
    if target_tract == ev_tract and target_stage == ev_stage:
        return True

    return False

def _is_status_eligible(c: dict) -> bool:
    """Who gets to 'vote' for STATUS."""
    et = c.get("event_type")
    st = c.get("status")

    if et == "capacity":
        return True  # capacity can always vote

    if et in {"facility"}:
        # Wind facilities can vote for all statuses; others only for paused/cancelled
        if c.get("product_lv1") == "wind":
            return True
        return st in PAUSELIKE          # only paused/cancelled can vote from facility

    if et in {"investment"}:
        return st in INV_PAUSELIKE      # investments can vote also if ongoing / announced but not completed

    # other event types (e.g., operations/construction) may vote
    return True

def events_product_union(events: list, field: str) -> list[str]:
    """
    Collect union of a product level from non-ignored events.

    Args:
        events: Event list from facility document.
        field: One of {"product_lv2", "product_lv3"}.
    """
    if field not in {"product_lv2", "product_lv3"}:
        raise ValueError(f"Unsupported field for product union: {field}")

    normalizer = normalize_pl2 if field == "product_lv2" else normalize_pl3
    acc = set()
    for ev in events or []:
        if phase_is_ignored(ev):
            continue
        acc.update(normalizer(ev.get(field)))

    return sorted(acc)

def collect_article_ids_from_summary(summary: dict) -> set:
    """
    Grab all non-null *_article_id values from a summary dict.
    """

    ids = set()
    for k, v in summary.items():
        if k.endswith("_article_id") and v is not None:
            ids.add(v)
    return ids

# ---------- main logic ------------

def build_phase_summary(events: list, phase_num: int | str | None, prev_capacity=None, prev_investment=None) -> dict | None:

    """
    Build a summary for one phase_num (or all events if phase=None).

    - Chooses the strongest status (lowest STATUS_RANK, then most recent date).
    - Capacity:
        if additional == False → take as total
        if additional == True  → add to prev_capacity
    - Investment:
        if is_total == True  → take as total
        if is_total == False → add to prev_investment
    - Adds earliest milestone dates (announce, under construction, operational).
    """

    # 1. filter for relevant phase events (valid data and user has not set ignored)
    phase_events = [c for c in events if _is_relevant_event(c, phase_num)]
    if not phase_events:
        return None

    # 2. sort events by i) status strength; ii) most recent date (could prefer capacity > investment > facility?)
    sorted_events = sorted(
        phase_events,
        key=lambda c: (
            STATUS_RANK[c["status"]], 
            -parse_date(c["date"]).timestamp())
    )

    # --------------- set STATUS -----------------
    # only consider facility and investment event types for paused or cancellation events
    status_rows = [c for c in sorted_events if _is_status_eligible(c)]
    best_status_row = (status_rows[0] if status_rows else sorted_events[0])

    # ------------- set CAPACITIES ----------------
    cap_rows = [
        c for c in phase_events
        if c.get("event_type") == "capacity" 
        and c.get("capacity") is not None
    ]
    # Sort: stronger status first, then most-recent date, totals preferred over additionals on tiebreak
    cap_rows.sort(
        key=lambda c: (
            STATUS_RANK.get(c.get("status"), len(STATUS_ORDER)),           # status strength
            -parse_date(c["date"]).timestamp(),                            # recency
            0 if c.get("additional") is False else 1                       # prefer totals
        )
    )

    capacity = None             # the cumulative capacity
    phase_capacity = None       # capacity specific to this phase 
    capacity_article_id = None  # initialise

    if cap_rows:
        latest = cap_rows[0]
        v = latest.get("capacity")          # the value
        add = latest.get("additional")      # is it an explicitly additional value
        capacity_article_id = latest.get("articleID")

        if add is True:
            # explicit incremental update
            phase_capacity = v
            capacity = (prev_capacity or 0) + v

        elif add is False:
            # explicit total after this phase
            if prev_capacity is not None:
                phase_capacity = max(v - prev_capacity, 0)
            else:
                phase_capacity = v
            capacity = v

    # ------------- set INVESTMENTS ----------------
    # set real investments
    inv_rows = sorted(
        [c for c in phase_events if c.get("event_type") != "facility" and c.get("investment") is not None],
        key=lambda c: (
            STATUS_RANK.get(c.get("status"), len(STATUS_ORDER)),
            -parse_date(c["date"]).timestamp(),
            0 if c.get("is_total") else 1
        )
    )

    # set the backup imputed investments
    imputed_rows = sorted(
        [c for c in phase_events if c.get("investment_imputed") is not None],
        key=lambda c: (
            STATUS_RANK.get(c.get("status"), len(STATUS_ORDER)),
            -parse_date(c["date"]).timestamp(),
            0 if c.get("is_total") else 1
        )
    )

    investment = None                       # the cumulative investment
    phase_investment = None                 # the investment specific to this phase
    investment_was_imputed = False          # did we have to impute the investment?

    # if there are real investments, store the best one
    if inv_rows:
        latest = inv_rows[0]
        v = latest.get("investment")
        total = latest.get("is_total")
        investment_article_id = latest.get("articleID")

    # otherwise, take the best implied investment
    elif imputed_rows:
        latest = imputed_rows[0]
        v = latest.get("investment_imputed")
        total = latest.get("is_total")
        investment_article_id = latest.get("articleID")
        investment_was_imputed = True

    else:
        latest = None
        v = None
        total = None
        investment_article_id = None

    if latest:
        if total is True:
            # explicit total after this phase
            if prev_investment is not None:
                phase_investment = max(v - prev_investment, 0)  # set phase_investment to the is_total value - prev_investment
            else:
                phase_investment = v
            investment = v   # set cumulative investment to the is_total value

        elif total is False:
            phase_investment = v                            # not total, set as phase investment
            investment = (prev_investment or 0) + v         # not total, add to cumulative investments

        # --- recalculate implied investment to better reflect specific project situation ---
        if investment_was_imputed and prev_investment is not None:
            if prev_capacity and capacity and prev_capacity > 0:
                implied_ratio = prev_investment / prev_capacity
                phase_investment = max((capacity - prev_capacity) * implied_ratio, 0)
                investment = prev_investment + phase_investment

    summary = {
        "status": best_status_row["status"],
        "status_article_id": best_status_row.get("articleID"),
        "phase_capacity": phase_capacity,
        "capacity": capacity,
        "capacity_article_id": capacity_article_id,
        "phase_investment": phase_investment,
        "investment": investment,
        "investment_was_imputed": investment_was_imputed,
        "investment_article_id": investment_article_id,
        "source_date": best_status_row["date"],
    }

    # For tract.stage phases (e.g., 'A.1', 'B.2'), attach union of product_lv2/lv3 within that phase
    tract, _ = parse_tract_stage(phase_num)
    if tract is not None:  # Only tracted phases get product_lv2/lv3
        summary["product_lv2"] = events_product_union(phase_events, "product_lv2")
        summary["product_lv3"] = events_product_union(phase_events, "product_lv3")
    
    # ------------- set CHRONOLOGY ----------------
    # add chronological milestone dates with two rules:
    # 1) construction can count as announcement if earlier (or announcement missing)
    # 2) if construction exists and operational is missing, set operational = construction + 2 years
    chron = sorted(status_rows, key=lambda c: parse_date(c["date"]))
    # we use status_rows (ie investment and facilities can vote only if paused | cancelled)
    # perhaps want to allow investments to vote for "ongoing" or "announced". Seems "completed" is the buggy one. 

    ann = next((c for c in chron if c["status"] == "announced"), None)
    uc  = next((c for c in chron if c["status"] == "under construction"), None)
    op  = next((c for c in chron if c["status"] == "operational"), None)

    summary["ann_date_imputed"] = False
    summary["uc_date_imputed"] = False
    summary["op_date_imputed"] = False

    # Rule 1: construction implies announcement if earlier or announcement missing
    if uc:
        uc_dt = parse_date(uc["date"])
        if (ann is None) or pd.isna(parse_date(ann["date"])) or (
            pd.notna(uc_dt) and uc_dt < parse_date(ann["date"])
        ):
            ann = uc

    if ann:
        summary["announced_on"] = ann["date"]
        summary["announced_article_id"] = ann.get("articleID")
    if uc:
        summary["under_construction_on"] = uc["date"]
        summary["under_construction_article_id"] = uc.get("articleID")

    if op:
        summary["operational_on"] = op["date"]
        summary["operational_article_id"] = op.get("articleID")
    elif uc:
        # Rule 2: no operational date → set to construction + 3 years
        uc_dt = parse_date(uc["date"])
        if pd.notna(uc_dt):
            op_dt = uc_dt + pd.DateOffset(years=3)
            summary["operational_on"] = op_dt.strftime("%Y-%m-%d")
            summary["op_date_imputed"] = True

    # --- Rule 3: backfill earlier milestones from an operational date ---
    if op:
        op_dt = parse_date(op["date"])
        if pd.notna(op_dt):
            ann_dt = parse_date(ann["date"]) if ann else None
            uc_dt  = parse_date(uc["date"]) if uc else None

            # Case A: both missing → set both to (op - 3 years)
            if ann_dt is None and uc_dt is None:
                backfill = (op_dt - pd.DateOffset(years=3)).strftime("%Y-%m-%d")
                summary["announced_on"] = backfill
                summary["under_construction_on"] = backfill
                summary["ann_date_imputed"] = True
                summary["uc_date_imputed"] = True

            # Case B: announced exists but construction missing
            elif ann_dt is not None and uc_dt is None:
                two_years_before = op_dt - pd.DateOffset(years=3)
                use_dt = ann_dt if ann_dt > two_years_before else two_years_before
                summary["under_construction_on"] = use_dt.strftime("%Y-%m-%d")
                summary["uc_date_imputed"] = True

    return summary

# ------ main ---------

def compute_summaries(debug_article_id: ObjectId | str | None = None):

    logging.info("🚀 Starting summary updates for main, phase 1 and phase 2...")

    updates = []

    query = {}
    if debug_article_id is not None:
        query = {"_id": debug_article_id if isinstance(debug_article_id, ObjectId) else ObjectId(debug_article_id)}
        logging.info(f"🐛 Debug mode: only processing _id={query['_id']}")

    for doc in facilities_collection.find(query):
        events = doc.get("events", [])
        if not events:
            continue

        update_fields: dict = {}
        unset_fields: dict = {}
        main_summary = None  #

        # normalize statuses (to compare investments and capacities)
        for c in events:
            if c.get("status") in STATUS_NORMALIZE:
                c["status"] = STATUS_NORMALIZE[c["status"]]

        # ---------- derive facility product_lv2 from NON-IGNORED events ----------
        current_pl2 = normalize_pl2(doc.get("product_lv2"))
        events_pl2 = events_product_union(events, "product_lv2")  # skips "ignore"
        if events_pl2 != current_pl2:
            update_fields["product_lv2"] = events_pl2
        current_pl3 = normalize_pl3(doc.get("product_lv3"))
        events_pl3 = events_product_union(events, "product_lv3")  # skips "ignore"
        if events_pl3 != current_pl3:
            update_fields["product_lv3"] = events_pl3
        # ------------------------------------------------------------------------

        # unique phase_num mentioned in the events, should be robust to string "ignore"
        phases_int = {pn for c in events if not phase_is_ignored(c) and (pn := phase_num_int(c)) is not None}
        phases_tract = {pn for c in events if not phase_is_ignored(c) and (pn := phase_num_tract_stage(c)) is not None}
        
        # Sort all phases: legacy ints first, then tract.stage (sorted by tract, then stage)
        def phase_sort_key(p):
            tract, stage = parse_tract_stage(p)
            return (tract or "", stage if stage is not None else 0)
        
        phases = sorted(phases_int, key=phase_sort_key) + sorted(phases_tract, key=phase_sort_key)

        # build summaries for each phase and store as a list under 'phases'
        # Maintain separate cumulative totals per tract
        phases_list = []
        tract_totals: dict[str | None, dict[str, float | None]] = {}  # {tract: {"capacity": ..., "investment": ...}}
        
        for p in phases:
            tract, stage = parse_tract_stage(p)
            
            # Get or initialize cumulative totals for this tract
            if tract not in tract_totals:
                tract_totals[tract] = {"capacity": None, "investment": None}
            
            prev_capacity = tract_totals[tract]["capacity"]
            prev_investment = tract_totals[tract]["investment"]
            
            summary = build_phase_summary(events, p, prev_capacity, prev_investment)
            if summary:
                # do not persist the helper field 'source_date' inside each phase object
                phase_obj = {"phase_num": p, **{k: v for k, v in summary.items() if k != "source_date"}}
                phases_list.append(phase_obj)

                # update rolling totals for this tract only
                if summary.get("capacity") is not None:
                    tract_totals[tract]["capacity"] = summary["capacity"]
                if summary.get("investment") is not None:
                    tract_totals[tract]["investment"] = summary["investment"]

        # --- attach comments from article docs to each phase summary ---
        if ATTACH_COMMENTS and phases_list:
            # 1) collect all article IDs used in any phase summary
            all_article_ids = set()
            for ph in phases_list:
                all_article_ids |= collect_article_ids_from_summary(ph)

            comments_by_id: dict = {}
            if all_article_ids:
                # normalize to ObjectId for querying by _id
                normalized_ids = []
                for v in all_article_ids:
                    if isinstance(v, ObjectId):
                        normalized_ids.append(v)
                    elif isinstance(v, str):
                        try:
                            normalized_ids.append(ObjectId(v))
                        except Exception:
                            # not a valid ObjectId string; skip
                            continue

                if normalized_ids:
                # batch query the articles once per facility
                    cursor = articles_collection.find(
                        {
                            ARTICLE_ID_FIELD: {"$in": normalized_ids},
                            "comment": {"$exists": True, "$ne": None, "$ne": ""},   # <- add this
                        },
                        {ARTICLE_ID_FIELD: 1, "comment": 1},
                    )
                    for art in cursor:
                        aid = art.get(ARTICLE_ID_FIELD)
                        comment = art.get("comment")
                        if aid is not None and comment:
                            comments_by_id[str(aid)] = comment

            # 2) attach per-phase comments mapping articleID -> comment
            for ph in phases_list:
                ids_for_phase = collect_article_ids_from_summary(ph)
                phase_comments = {
                    str(aid): comments_by_id[str(aid)]
                    for aid in ids_for_phase
                    if str(aid) in comments_by_id
                }
                if phase_comments:
                    ph["comments"] = phase_comments

        update_fields["phases"] = phases_list

        # ---------- build "main" summary from phases list ----------
        if phases_list:
            selected = None
            prev_oper = None            # a previously operational phase
            for ph in phases_list:
                st = ph.get("status")
                # if the current phase is operational move on (but store as latest operational)
                if st == "operational":
                    prev_oper = ph  # keep latest operational seen so far
                    continue
                #  non-operational phase encountered. stop and take this phase, or a previous operational if exists.
                selected = prev_oper if prev_oper is not None else ph
                break
            else:
                # never hit a non-operational → take the last phase
                selected = phases_list[-1]

            # earliest dates across all phases
            def _earliest(phases, key):
                dts = [parse_date(p.get(key)) for p in phases if p.get(key)]
                dts = [d for d in dts if pd.notna(d)]
                return min(dts).strftime("%Y-%m-%d") if dts else None

            main_summary = {
                "status": selected.get("status"),
                "capacity": selected.get("capacity"),
                "investment": selected.get("investment"),
                "investment_was_imputed": selected.get("investment_was_imputed", False),
                "announced_on": _earliest(phases_list, "announced_on"),
                "under_construction_on": _earliest(phases_list, "under_construction_on"),
                "operational_on": _earliest(phases_list, "operational_on"),
                "main_from_phase_num": selected.get("phase_num"),  # optional provenance; drop if you prefer
            }

            update_fields["main"] = main_summary
        else:
            # no phases → ensure main is unset to avoid staleness
            if "main" in doc:
                unset_fields["main"] = ""

        # Queue update with both $set and $unset. With $set we are always overwriting.
        if update_fields or unset_fields:
            update_op = {}
            if update_fields:
                update_op["$set"] = update_fields
            if unset_fields:
                update_op["$unset"] = unset_fields  # CHANGED: remove stale phases/main
            updates.append(UpdateOne({"_id": doc["_id"]}, update_op))

    if updates:
        result = facilities_collection.bulk_write(updates)
        logging.info(f"✅ Updated summaries for {result.modified_count} facilities.")
    else:
        logging.info("⚠️ No facilities needed updates.")

if __name__ == "__main__":
    compute_summaries("690342d840aff9ca9a4e7f29")