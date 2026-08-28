from datetime import datetime, timezone, date, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, Query
from bson import ObjectId

from db import db
from crud_base import doc_out, is_oid
from security import require_permission, get_current_user, user_school_scope

router = APIRouter(prefix="/dashboard")

JKT = ZoneInfo("Asia/Jakarta")


async def _resolve_period(period_id: str = None):
    doc = None
    if period_id and is_oid(period_id):
        doc = await db.periods.find_one({"_id": ObjectId(period_id)})
    if not doc:
        doc = await db.periods.find_one({"status": "ACTIVE", "is_test": {"$ne": True}})
    return doc_out(doc) if doc else None


@router.get("/summary", dependencies=[Depends(require_permission("DASHBOARD_VIEW"))])
async def summary(period_id: str = Query(default=None), the_date: str = Query(default=None),
                  user: dict = Depends(get_current_user)):
    period = await _resolve_period(period_id)

    try:
        d = datetime.fromisoformat(the_date).date() if the_date else datetime.now(JKT).date()
    except Exception:
        d = datetime.now(JKT).date()
    is_ahad = d.weekday() == 6  # Sunday (Ahad)

    scope = user_school_scope(user)
    school_query: dict = {"status": "ACTIVE"}
    if scope is not None:
        school_query["_id"] = {"$in": [ObjectId(s) for s in scope if is_oid(s)]}

    schools_count = await db.schools.count_documents(school_query)
    teachers_count = await db.teachers.count_documents({"status": "ACTIVE"})
    vehicles_count = await db.vehicles.count_documents({"status": "ACTIVE"})
    dh_count = await db.daily_board_members.count_documents({"status": "ACTIVE"})
    officers_count = await db.officers.count_documents({"status": "ACTIVE"})

    # ---- schedule-driven operational data (period + scope) ----
    scope_ids = [ObjectId(s) for s in scope if is_oid(s)] if scope is not None else None
    sched_base = {}
    if period:
        sched_base["period_id"] = period["id"]
    if scope is not None:
        sched_base["school_id"] = {"$in": [str(x) for x in scope_ids]}

    today_str = d.isoformat()
    tomorrow_str = (d + timedelta(days=1)).isoformat()

    async def _fetch(day):
        q = {**sched_base, "date": day, "status": {"$ne": "CANCELLED"}}
        return [doc_out(x) async for x in db.schedules.find(q).sort("start_time", 1)]

    today_sched = await _fetch(today_str) if period else []
    tomorrow_sched = await _fetch(tomorrow_str) if period else []

    started = [s for s in today_sched if s.get("status") in ("ONGOING", "COMPLETED")]
    today_total = len(today_sched)
    unconfirmed_today = [s for s in today_sched if s.get("status") == "PLANNED"]

    rencana_items = [
        {"school_name": s.get("school_name"), "date": s.get("date"),
         "start_time": s.get("start_time"), "end_time": s.get("end_time"),
         "status": s.get("status")}
        for s in tomorrow_sched
    ]

    perlu_perhatian = []
    if not is_ahad and len(unconfirmed_today) > 0:
        perlu_perhatian.append({
            "type": "SCHEDULE_UNCONFIRMED",
            "message": f"{len(unconfirmed_today)} jadwal hari ini belum dikonfirmasi",
        })

    # Recent activity (audit) - only for users who can view audit
    recent = []
    from permissions import has_permission
    if has_permission(user.get("role"), "AUDIT_VIEW"):
        cursor = db.audit_logs.find({}).sort("timestamp", -1).limit(8)
        recent = [doc_out(x) async for x in cursor]

    return {
        "period": period,
        "is_test_mode": bool(period.get("is_test")) if period else False,
        "date": d.isoformat(),
        "is_ahad": is_ahad,
        "cards": {
            "schools": {"label": "Sekolah", "value": schools_count},
            "teachers": {"label": "Pengajar", "value": teachers_count},
            "vehicles": {"label": "Armada", "value": vehicles_count},
            "daily_board": {"label": "Dewan Harian", "value": dh_count},
            "officers": {"label": "Petugas", "value": officers_count},
        },
        "realisasi": {
            "schools_started": len(started), "schools_total": today_total,
            "teachers_departed": 0, "teachers_total": 0,
            "vehicles_departed": 0, "vehicles_total": 0,
            "present": 0, "absent": 0, "replaced": 0,
            "monitoring_submitted": 0, "documentation_complete": 0,
        },
        "rencana_besok": {
            "date": tomorrow_str,
            "schools": len(tomorrow_sched),
            "teachers": 0, "vehicles": 0,
            "items": rencana_items,
            "available": len(tomorrow_sched) > 0,
        },
        "plan_vs_realization": [
            {"label": "Sekolah", "planned": today_total, "actual": len(started),
             "diff": len(started) - today_total},
        ] if period else [],
        "perlu_perhatian": perlu_perhatian,
        "recent_activity": recent,
        "operational_ready": bool(period),
    }
