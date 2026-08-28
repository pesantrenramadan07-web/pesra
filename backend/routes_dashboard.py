from datetime import datetime, timezone, date
from fastapi import APIRouter, Depends, Query
from bson import ObjectId

from db import db
from crud_base import doc_out, is_oid
from security import require_permission, get_current_user, user_school_scope

router = APIRouter(prefix="/dashboard")


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
        d = datetime.fromisoformat(the_date).date() if the_date else datetime.now(timezone.utc).date()
    except Exception:
        d = datetime.now(timezone.utc).date()
    is_ahad = d.weekday() == 6  # Sunday

    scope = user_school_scope(user)
    school_query: dict = {"status": "ACTIVE"}
    if scope is not None:
        school_query["_id"] = {"$in": [ObjectId(s) for s in scope if is_oid(s)]}

    schools_count = await db.schools.count_documents(school_query)
    teachers_count = await db.teachers.count_documents({"status": "ACTIVE"})
    vehicles_count = await db.vehicles.count_documents({"status": "ACTIVE"})
    dh_count = await db.daily_board_members.count_documents({"status": "ACTIVE"})
    officers_count = await db.officers.count_documents({"status": "ACTIVE"})

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
            "schools_started": 0, "schools_total": schools_count,
            "teachers_departed": 0, "teachers_total": teachers_count,
            "vehicles_departed": 0, "vehicles_total": vehicles_count,
            "present": 0, "absent": 0, "replaced": 0,
            "monitoring_submitted": 0, "documentation_complete": 0,
        },
        "rencana_besok": {
            "schools": 0, "teachers": 0, "vehicles": 0, "items": [],
            "available": False,
        },
        "plan_vs_realization": [],
        "perlu_perhatian": [],
        "recent_activity": recent,
        "operational_ready": False,
    }
