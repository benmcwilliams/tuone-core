import math
import pandas as pd
from pymongo import UpdateOne

# ---------- constants ----------
INV_TO_UNIFIED = {"completed": "operational", "ongoing": "under construction"}
STATUS_ORDER = ["cancelled", "paused", "operational", "under construction", "announced", "unclear"]
STATUS_RANK = {s: i for i, s in enumerate(STATUS_ORDER)}

# ---------- tiny helpers ----------
def _pd_time(x):
    try:
        return pd.to_datetime(x)
    except Exception:
        return pd.NaT

def _as_float(x):
    if x is None:
        return None
    sx = str(x).strip()
    if not sx:
        return None
    try:
        return float(sx)
    except Exception:
        return None

def _unify_status(raw, event_type):
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return None
    if not isinstance(raw, str):
        return None
    s = raw.strip().lower()
    if event_type == "investment":
        s = INV_TO_UNIFIED.get(s, s)
    return s if s in STATUS_RANK else None

def _status_vote(rows):
    """Strongest status wins; tie-break by latest date."""
    rows = [r for r in rows if r.get("status_u") and pd.notna(r.get("date"))]
    if not rows:
        return None
    rows.sort(key=lambda r: (STATUS_RANK[r["status_u"]], -r["date"].timestamp()))
    return rows[0]["status_u"]

def _earliest_date(rows, status):
    pool = [r for r in rows if r.get("status_u") == status and pd.notna(r.get("date"))]
    if not pool:
        return None
    pool.sort(key=lambda r: r["date"])
    return pool[0]["date"].date().isoformat()

# ---------- core logic ----------
def _normalize_events(events):
    out = []
    for e in events or []:
        et = (e.get("event_type") or "").lower()
        out.append({
            "event_type": et,
            "phase_num": e.get("phase_num"),
            "status_u": _unify_status(e.get("status"), et),
            "date": _pd_time(e.get("date") or e.get("date_str")),
            "capacity": _as_float(e.get("capacity_normalized")),
            "additional": e.get("additional"),                # True=increment, False=total
            "is_total": bool(e.get("is_total")),             # can exist on capacity or investment
            "amount_eur": _as_float(
                e.get("amount_EUR") if e.get("amount_EUR") is not None else e.get("amount_EUR_imputed")
            ),
        })
    return out

def summarise_phase(events_phase, prev_capacity=None, prev_investment=None):
    """Summarise a single phase, returning increments + cumulative totals."""
    rows = [r for r in events_phase if pd.notna(r["date"])]
    if not rows:
        return {}

    # status
    status = _status_vote(rows)

    # capacity increment = latest additional == True
    caps_inc = [
        r for r in rows
        if r["event_type"] == "capacity"
        and r.get("additional") is True
        and r["capacity"] is not None
    ]
    caps_inc.sort(key=lambda r: r["date"], reverse=True)
    capacity_increment = caps_inc[0]["capacity"] if caps_inc else None

    # cumulative capacity = prev + increment (if any)
    capacity_reached = prev_capacity or 0
    if capacity_increment is not None:
        capacity_reached += capacity_increment
    if capacity_reached == 0:
        capacity_reached = None  # if still empty

    # investment increment = latest is_total == False
    inv_inc = [
        r for r in rows
        if r["event_type"] == "investment"
        and r.get("is_total") is False
        and r["amount_eur"] is not None
    ]
    inv_inc.sort(key=lambda r: r["date"], reverse=True)
    investment_increment = inv_inc[0]["amount_eur"] if inv_inc else None

    # cumulative investment = prev + increment (if any)
    investment_reached = prev_investment or 0
    if investment_increment is not None:
        investment_reached += investment_increment
    if investment_reached == 0:
        investment_reached = None

    return {
        "status": status,
        "capacity_increment": capacity_increment,
        "capacity_reached": capacity_reached,
        "investment_increment": investment_increment,
        "investment_reached": investment_reached,
        "dt_announce": _earliest_date(rows, "announced"),
        "dt_construct": _earliest_date(rows, "under construction"),
        "dt_operational": _earliest_date(rows, "operational"),
    }

def build_phase_summaries_for_doc(doc: dict) -> dict:
    rows = _normalize_events(doc.get("events") or [])

    summaries = {}
    prev_capacity, prev_investment = 0, 0
    for p in sorted({int(r["phase_num"]) for r in rows if str(r.get("phase_num")).isdigit()}):
        phase_rows = [r for r in rows if str(r.get("phase_num")) == str(p)]
        summary = summarise_phase(phase_rows, prev_capacity, prev_investment)
        summaries[f"phase_{p}"] = summary

        # update baselines for next phase
        if summary.get("capacity_reached") is not None:
            prev_capacity = summary["capacity_reached"]
        if summary.get("investment_reached") is not None:
            prev_investment = summary["investment_reached"]

    # main view: strongest status, latest total capacity, latest total investment
    main_status = _status_vote(rows)

    caps_total = [
        r for r in rows
        if r["event_type"] == "capacity"
        and r["capacity"] is not None
        and r.get("additional") is False
    ]
    caps_total.sort(key=lambda r: r["date"], reverse=True)
    main_capacity = caps_total[0]["capacity"] if caps_total else None

    inv_total = [
        r for r in rows
        if r["event_type"] == "investment"
        and r.get("is_total") is True
        and r["amount_eur"] is not None
    ]
    inv_total.sort(key=lambda r: r["date"], reverse=True)
    main_investment = inv_total[0]["amount_eur"] if inv_total else None

    main = {
        "status": main_status,
        "capacity": main_capacity,
        "investment_total": main_investment,
        "announced_on": _earliest_date(rows, "announced"),
        "under_construction_on": _earliest_date(rows, "under construction"),
        "operational_on": _earliest_date(rows, "operational"),
    }

    return {"phases": summaries, "main": main}

def write_phase_summaries(facilities_collection, query=None, dry_run=True, limit=None):
    q = query or {}
    cur = facilities_collection.find(q)
    if limit:
        cur = cur.limit(limit)

    updates, matched = [], 0
    for doc in cur:
        out = build_phase_summaries_for_doc(doc)
        if out["phases"] or out["main"]:
            matched += 1
            updates.append(UpdateOne({"_id": doc["_id"]}, {"$set": {"phase_summaries": out["phases"], "main": out["main"]}}))

    if dry_run or not updates:
        return matched, 0
    res = facilities_collection.bulk_write(updates)
    return matched, res.modified_count