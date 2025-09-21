import pandas as pd
import math
from pymongo import UpdateOne

# ---- Unified status logic ----
INV_TO_UNIFIED = {
    "completed": "operational",
    "ongoing": "under construction",
}

UNIFIED_STATUS_ORDER = [
    "cancelled",
    "paused",
    "operational",          # includes investment 'completed'
    "under construction",   # includes investment 'ongoing'
    "announced",
    "unclear",
]
UNIFIED_RANK = {s: i for i, s in enumerate(UNIFIED_STATUS_ORDER)}

def _parse_date(d):
    if d is None or (isinstance(d, float) and math.isnan(d)):
        return pd.NaT
    try:
        return pd.to_datetime(d)
    except Exception:
        return pd.NaT

def _unify_status(status, event_type: str) -> str | None:
    # treat None / NaN as missing
    if status is None:
        return None
    if isinstance(status, float) and (math.isnan(status) or status == float("inf") or status == float("-inf")):
        return None
    if not isinstance(status, str):
        return None  # only accept proper strings

    s = status.strip().lower()
    if event_type == "investment":
        s = INV_TO_UNIFIED.get(s, s)
    return s if s in UNIFIED_RANK else None

def _as_float(x):
    if x is None:
        return None
    try:
        sx = str(x).strip()
        if sx == "":
            return None
        return float(sx)
    except Exception:
        return None

# ---- Per-phase summary ----
def summarise_phase(events_phase: list, prev_reached: float | None) -> dict:
    """
    events_phase: events for a single phase_num with keys like:
      - event_type in {"capacity","investment"}
      - status, date, phase_num
      - capacity_normalized (number)
      - amount_EUR (number) [and optionally amount_EUR_imputed]
      - additional (bool) for capacity
      - is_total (bool) for investment
    """
    # Normalize minimal fields we need
    norm = []
    for e in events_phase:
        et = (e.get("event_type") or "").lower()
        status_u = _unify_status(e.get("status"), et)
        dt = _parse_date(e.get("date") or e.get("date_str"))

        cap_val = _as_float(e.get("capacity_normalized"))
        # investment value: prefer amount_EUR, else amount_EUR_imputed if present
        inv_val = e.get("amount_EUR")
        if inv_val is None and "amount_EUR_imputed" in e:
            inv_val = e.get("amount_EUR_imputed")
        inv_val = _as_float(inv_val)

        additional = e.get("additional")  # may be None; we only use explicit True/False
        is_total = e.get("is_total")
        if is_total is None:
            is_total = False

        norm.append({
            "event_type": et,
            "status_u": status_u,
            "date": dt,
            "capacity_normalized": cap_val,
            "amount_EUR": inv_val,
            "additional": additional,
            "is_total": is_total,
        })

    # ---- Unified status: strongest rank, then latest date ----
    status_candidates = [x for x in norm if x["status_u"] and pd.notna(x["date"])]
    phase_status = None
    if status_candidates:
        status_candidates.sort(key=lambda x: (UNIFIED_RANK[x["status_u"]], -x["date"].timestamp()))
        phase_status = status_candidates[0]["status_u"]

    # ---- Capacities ----
    caps = [x for x in norm if x["event_type"] == "capacity" and x["capacity_normalized"] is not None and pd.notna(x["date"])]

    # explicit reached (additional == False), latest by date
    reached_candidates = [c for c in caps if c.get("additional") is False]
    reached_candidates.sort(key=lambda x: x["date"], reverse=True)
    capacity_reached = reached_candidates[0]["capacity_normalized"] if reached_candidates else None

    # explicit additional (additional == True), latest by date (tie-break by stronger status)
    add_candidates = [c for c in caps if c.get("additional") is True]
    add_candidates.sort(
        key=lambda x: (
            x["date"],
            -UNIFIED_RANK.get(x["status_u"] or "unclear", 99)
        ),
        reverse=True
    )
    capacity_additional = add_candidates[0]["capacity_normalized"] if add_candidates else None

    # Fallback for reached: compute incrementally from previous phases
    if capacity_reached is None:
        if prev_reached is not None and capacity_additional is not None:
            capacity_reached = prev_reached + capacity_additional
        elif prev_reached is not None and capacity_additional is None:
            capacity_reached = prev_reached  # carry forward baseline

    # ---- Investments ----
    invs = [x for x in norm if x["event_type"] == "investment" and x["amount_EUR"] is not None and pd.notna(x["date"])]

    total_candidates = [i for i in invs if i["is_total"] is True]
    total_candidates.sort(key=lambda x: x["date"], reverse=True)
    investment_total = total_candidates[0]["amount_EUR"] if total_candidates else None

    incr_candidates = [i for i in invs if i["is_total"] is False]
    incr_candidates.sort(key=lambda x: x["date"], reverse=True)
    investment_incremental = incr_candidates[0]["amount_EUR"] if incr_candidates else None

    # ---- Milestones (earliest within the phase across both types) ----
    dated = [x for x in norm if x["status_u"] and pd.notna(x["date"])]

    def earliest(*statuses) -> str | None:
        pool = [x for x in dated if x["status_u"] in set(statuses)]
        if not pool:
            return None
        pool.sort(key=lambda x: x["date"])
        return pool[0]["date"].date().isoformat()

    dt_announce = earliest("announced")
    dt_construct = earliest("under construction")  # 'ongoing' already mapped to UC
    dt_operational = earliest("operational")       # 'completed' already mapped to operational

    return {
        "status": phase_status,
        "capacity_additional": capacity_additional,
        "capacity_reached": capacity_reached,
        "investment_incremental": investment_incremental,
        "investment_total": investment_total,
        "dt_announce": dt_announce,
        "dt_construct": dt_construct,
        "dt_operational": dt_operational,
    }

# ---- Driver over a document (events only) ----
def build_phase_summaries_for_doc(doc: dict) -> dict:
    """
    Returns {"phases": {"phase_1": {...}, "phase_2": {...}, ...}}
    Requires doc["events"] with event dicts containing phase_num.
    """
    events = (doc.get("events") or [])
    # require a phase number
    def safe_phase_num(e):
        try:
            return int(e.get("phase_num"))
        except Exception:
            return None
    events = [e for e in events if safe_phase_num(e) is not None]

    phase_nums = sorted({safe_phase_num(e) for e in events})
    summaries = {}
    prev_reached = None
    for p in phase_nums:
        phase_events = [e for e in events if safe_phase_num(e) == p]
        summary = summarise_phase(phase_events, prev_reached=prev_reached)
        summaries[f"phase_{p}"] = summary
        if summary.get("capacity_reached") is not None:
            prev_reached = summary["capacity_reached"]

    return {"phases": summaries}

# ---- Optional: bulk write helper ----
def write_phase_summaries(facilities_collection, query: dict | None = None, dry_run: bool = True, limit: int | None = None):
    q = query or {}
    cursor = facilities_collection.find(q)
    if limit:
        cursor = cursor.limit(limit)

    updates = []
    n = 0
    for doc in cursor:
        out = build_phase_summaries_for_doc(doc)
        if out["phases"]:
            n += 1
            updates.append(UpdateOne({"_id": doc["_id"]}, {"$set": {"phase_summaries": out["phases"]}}))

    if dry_run or not updates:
        return n, 0  # (matched, modified)
    res = facilities_collection.bulk_write(updates)
    return n, res.modified_count