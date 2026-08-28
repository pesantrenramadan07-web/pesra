from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from bson import ObjectId

from db import db
from crud_base import doc_out, oid, is_oid
from security import require_permission, get_current_user, user_school_scope, enforce_school_scope
from audit import log_audit
from models import ScheduleIn

router = APIRouter(prefix="/schedules")

STATUSES = ["PLANNED", "CONFIRMED", "ONGOING", "COMPLETED", "CANCELLED"]
TRANSITIONS = {
    "PLANNED": ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["ONGOING", "CANCELLED", "PLANNED"],
    "ONGOING": ["COMPLETED", "CANCELLED"],
    "COMPLETED": [],
    "CANCELLED": [],
}


def _now():
    return datetime.now(timezone.utc).isoformat()


async def _school_name(school_id):
    s = await db.schools.find_one({"_id": oid(school_id)})
    return s.get("name") if s else None


async def _period_name(period_id):
    p = await db.periods.find_one({"_id": oid(period_id)})
    return p.get("name") if p else None


@router.get("", dependencies=[Depends(require_permission("SCHEDULE_VIEW"))])
async def list_schedules(period_id: str = Query(default=None), date: str = Query(default=None),
                         school_id: str = Query(default=None), status: str = Query(default=None),
                         search: str = Query(default=""), page: int = 1, limit: int = 50,
                         user: dict = Depends(get_current_user)):
    query: dict = {}
    if period_id and is_oid(period_id):
        query["period_id"] = period_id
    if date:
        query["date"] = date
    if status:
        query["status"] = status
    scope = user_school_scope(user)
    if school_id and is_oid(school_id):
        if scope is not None and school_id not in scope:
            raise HTTPException(status_code=403, detail="Sekolah di luar cakupan Anda")
        query["school_id"] = school_id
    elif scope is not None:
        query["school_id"] = {"$in": scope}
    if search:
        query["school_name"] = {"$regex": search, "$options": "i"}
    total = await db.schedules.count_documents(query)
    cursor = db.schedules.find(query).sort([("date", -1), ("start_time", 1)]).skip((page - 1) * limit).limit(min(limit, 200))
    items = [doc_out(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.get("/{schedule_id}", dependencies=[Depends(require_permission("SCHEDULE_VIEW"))])
async def get_schedule(schedule_id: str, user: dict = Depends(get_current_user)):
    doc = await db.schedules.find_one({"_id": oid(schedule_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan")
    enforce_school_scope(user, doc.get("school_id"))
    return doc_out(doc)


@router.get("/{schedule_id}/history", dependencies=[Depends(require_permission("SCHEDULE_VIEW"))])
async def schedule_history(schedule_id: str):
    cursor = db.schedule_history.find({"schedule_id": schedule_id}).sort("changed_at", -1)
    return [doc_out(d) async for d in cursor]


@router.post("", dependencies=[Depends(require_permission("SCHEDULE_CREATE"))])
async def create_schedule(payload: ScheduleIn, request: Request, user: dict = Depends(get_current_user)):
    if not is_oid(payload.period_id) or not await db.periods.find_one({"_id": ObjectId(payload.period_id)}):
        raise HTTPException(status_code=404, detail="Periode tidak ditemukan")
    if not is_oid(payload.school_id):
        raise HTTPException(status_code=404, detail="Sekolah tidak valid")
    school = await db.schools.find_one({"_id": ObjectId(payload.school_id)})
    if not school:
        raise HTTPException(status_code=404, detail="Sekolah tidak ditemukan")
    enforce_school_scope(user, payload.school_id)
    if payload.status not in STATUSES:
        raise HTTPException(status_code=422, detail="Status jadwal tidak valid")
    if not payload.date:
        raise HTTPException(status_code=422, detail="Tanggal wajib diisi")
    # duplicate protection: one schedule per period+school+date
    dup = await db.schedules.find_one({
        "period_id": payload.period_id, "school_id": payload.school_id,
        "date": payload.date, "status": {"$ne": "CANCELLED"}})
    if dup:
        raise HTTPException(status_code=409, detail="Jadwal untuk sekolah & tanggal ini sudah ada")
    doc = payload.model_dump()
    doc["school_name"] = school.get("name")
    doc["period_name"] = await _period_name(payload.period_id)
    doc["created_at"] = _now()
    doc["updated_at"] = _now()
    doc["created_by"] = user["id"]
    res = await db.schedules.insert_one(doc)
    await log_audit(user, "CREATE", "SCHEDULE", "schedule", res.inserted_id, None, doc, request)
    return doc_out(await db.schedules.find_one({"_id": res.inserted_id}))


@router.put("/{schedule_id}", dependencies=[Depends(require_permission("SCHEDULE_UPDATE"))])
async def update_schedule(schedule_id: str, payload: ScheduleIn, request: Request, user: dict = Depends(get_current_user)):
    old = await db.schedules.find_one({"_id": oid(schedule_id)})
    if not old:
        raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan")
    enforce_school_scope(user, old.get("school_id"))
    if not is_oid(payload.school_id):
        raise HTTPException(status_code=404, detail="Sekolah tidak valid")
    school = await db.schools.find_one({"_id": ObjectId(payload.school_id)})
    if not school:
        raise HTTPException(status_code=404, detail="Sekolah tidak ditemukan")
    enforce_school_scope(user, payload.school_id)
    dup = await db.schedules.find_one({
        "period_id": old["period_id"], "school_id": payload.school_id,
        "date": payload.date, "status": {"$ne": "CANCELLED"},
        "_id": {"$ne": oid(schedule_id)}})
    if dup:
        raise HTTPException(status_code=409, detail="Jadwal untuk sekolah & tanggal ini sudah ada")
    update = payload.model_dump()
    update["period_id"] = old["period_id"]  # period cannot change on edit
    update["period_name"] = old.get("period_name")
    update["school_name"] = school.get("name")
    update["updated_at"] = _now()
    update["updated_by"] = user["id"]
    await db.schedules.update_one({"_id": oid(schedule_id)}, {"$set": update})
    await db.schedule_history.insert_one({
        "schedule_id": schedule_id, "change_type": "UPDATE",
        "old_value": {k: old.get(k) for k in ["date", "start_time", "end_time", "status", "school_id", "notes"]},
        "new_value": {k: update.get(k) for k in ["date", "start_time", "end_time", "status", "school_id", "notes"]},
        "changed_by": user["id"], "changed_by_name": user["name"], "changed_at": _now(),
    })
    await log_audit(user, "UPDATE", "SCHEDULE", "schedule", schedule_id, doc_out(dict(old)), update, request)
    return doc_out(await db.schedules.find_one({"_id": oid(schedule_id)}))


@router.post("/{schedule_id}/status", dependencies=[Depends(require_permission("SCHEDULE_UPDATE"))])
async def set_status(schedule_id: str, request: Request, status: str = Query(...),
                     reason: str = Query(default=""), user: dict = Depends(get_current_user)):
    if status not in STATUSES:
        raise HTTPException(status_code=422, detail="Status jadwal tidak valid")
    old = await db.schedules.find_one({"_id": oid(schedule_id)})
    if not old:
        raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan")
    enforce_school_scope(user, old.get("school_id"))
    cur = old.get("status")
    if status == cur:
        return {"message": f"Status jadwal sudah {status}"}
    if status not in TRANSITIONS.get(cur, []):
        raise HTTPException(status_code=409,
            detail=f"Transisi status {cur} → {status} tidak diizinkan")
    await db.schedules.update_one({"_id": oid(schedule_id)},
        {"$set": {"status": status, "updated_at": _now(), "updated_by": user["id"]}})
    await db.schedule_history.insert_one({
        "schedule_id": schedule_id, "change_type": "STATUS",
        "old_value": {"status": cur}, "new_value": {"status": status}, "reason": reason,
        "changed_by": user["id"], "changed_by_name": user["name"], "changed_at": _now(),
    })
    await log_audit(user, "UPDATE", "SCHEDULE", "schedule", schedule_id,
                    {"status": cur}, {"status": status}, request)
    return {"message": f"Status jadwal diubah menjadi {status}"}


@router.delete("/{schedule_id}", dependencies=[Depends(require_permission("SCHEDULE_UPDATE"))])
async def cancel_schedule(schedule_id: str, request: Request, user: dict = Depends(get_current_user)):
    old = await db.schedules.find_one({"_id": oid(schedule_id)})
    if not old:
        raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan")
    enforce_school_scope(user, old.get("school_id"))
    if old.get("status") in ("COMPLETED", "CANCELLED"):
        raise HTTPException(status_code=409, detail="Jadwal selesai/dibatalkan tidak dapat dibatalkan lagi")
    await db.schedules.update_one({"_id": oid(schedule_id)},
        {"$set": {"status": "CANCELLED", "updated_at": _now(), "updated_by": user["id"]}})
    await log_audit(user, "UPDATE", "SCHEDULE", "schedule", schedule_id,
                    {"status": old.get("status")}, {"status": "CANCELLED"}, request)
    return {"message": "Jadwal dibatalkan"}
