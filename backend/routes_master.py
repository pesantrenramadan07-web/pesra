from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from bson import ObjectId

from db import db
from crud_base import doc_out, oid, is_oid
from security import require_permission, get_current_user, user_school_scope
from audit import log_audit
from models import PeriodIn, SchoolIn, TeacherIn, DailyBoardIn, OfficerIn, VehicleIn

router = APIRouter()


def _now():
    return datetime.now(timezone.utc).isoformat()


async def _list(coll_name, module, request, user, search, status, page, limit,
                search_fields, scoped=False):
    coll = db[coll_name]
    query: dict = {}
    if search and search_fields:
        query["$or"] = [{f: {"$regex": search, "$options": "i"}} for f in search_fields]
    if status:
        query["status"] = status
    if scoped:
        scope = user_school_scope(user)
        if scope is not None:
            ids = [ObjectId(s) for s in scope if is_oid(s)]
            query["_id"] = {"$in": ids}
    total = await coll.count_documents(query)
    skip = max(0, (page - 1) * limit)
    cursor = coll.find(query).sort("created_at", -1).skip(skip).limit(min(limit, 200))
    items = [doc_out(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "limit": limit}


async def _create(coll_name, module, entity, payload: dict, user, request):
    payload["status"] = payload.get("status", "ACTIVE")
    payload["created_at"] = _now()
    payload["updated_at"] = _now()
    payload["created_by"] = user["id"]
    res = await db[coll_name].insert_one(payload)
    doc = await db[coll_name].find_one({"_id": res.inserted_id})
    # motor mutates payload to inject _id; strip before audit to keep audit JSON-serialisable
    audit_payload = {k: v for k, v in payload.items() if k != "_id"}
    await log_audit(user, "CREATE", module, entity, res.inserted_id, None, audit_payload, request)
    return doc_out(doc)


async def _update(coll_name, module, entity, item_id, payload: dict, user, request):
    coll = db[coll_name]
    old = await coll.find_one({"_id": oid(item_id)})
    if not old:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")
    payload["updated_at"] = _now()
    payload["updated_by"] = user["id"]
    await coll.update_one({"_id": oid(item_id)}, {"$set": payload})
    doc = await coll.find_one({"_id": oid(item_id)})
    await log_audit(user, "UPDATE", module, entity, item_id, doc_out(dict(old)), payload, request)
    return doc_out(doc)


async def _archive(coll_name, module, entity, item_id, user, request):
    coll = db[coll_name]
    old = await coll.find_one({"_id": oid(item_id)})
    if not old:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")
    await coll.update_one({"_id": oid(item_id)},
                          {"$set": {"status": "INACTIVE", "archived_at": _now(), "updated_at": _now()}})
    await log_audit(user, "ARCHIVE", module, entity, item_id, {"status": old.get("status")},
                    {"status": "INACTIVE"}, request)
    return {"message": "Data berhasil diarsipkan"}


# =================== PERIODS ===================
@router.get("/periods", dependencies=[Depends(require_permission("PERIOD_VIEW"))])
async def list_periods(request: Request, search: str = "", status: str = "",
                       include_test: bool = True, page: int = 1, limit: int = 100,
                       user: dict = Depends(get_current_user)):
    query: dict = {}
    if search:
        query["$or"] = [{"name": {"$regex": search, "$options": "i"}},
                        {"hijri_year": {"$regex": search, "$options": "i"}}]
    if status:
        query["status"] = status
    if not include_test:
        query["is_test"] = {"$ne": True}
    total = await db.periods.count_documents(query)
    cursor = db.periods.find(query).sort("start_date", -1).skip((page - 1) * limit).limit(min(limit, 200))
    items = [doc_out(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.get("/periods/active")
async def active_period(user: dict = Depends(get_current_user)):
    doc = await db.periods.find_one({"status": "ACTIVE", "is_test": {"$ne": True}})
    return doc_out(doc) if doc else None


@router.get("/periods/{item_id}", dependencies=[Depends(require_permission("PERIOD_VIEW"))])
async def get_period(item_id: str):
    doc = await db.periods.find_one({"_id": oid(item_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Periode tidak ditemukan")
    return doc_out(doc)


@router.post("/periods", dependencies=[Depends(require_permission("PERIOD_CREATE"))])
async def create_period(payload: PeriodIn, request: Request, user: dict = Depends(get_current_user)):
    return await _create("periods", "PERIOD", "period", payload.model_dump(), user, request)


@router.put("/periods/{item_id}", dependencies=[Depends(require_permission("PERIOD_UPDATE"))])
async def update_period(item_id: str, payload: PeriodIn, request: Request, user: dict = Depends(get_current_user)):
    return await _update("periods", "PERIOD", "period", item_id, payload.model_dump(), user, request)


@router.post("/periods/{item_id}/status", dependencies=[Depends(require_permission("PERIOD_MANAGE"))])
async def set_period_status(item_id: str, request: Request, status: str = Query(...),
                            user: dict = Depends(get_current_user)):
    valid = ["DRAFT", "TESTING", "HISTORICAL", "ACTIVE", "COMPLETED", "ARCHIVED"]
    if status not in valid:
        raise HTTPException(status_code=422, detail="Status periode tidak valid")
    old = await db.periods.find_one({"_id": oid(item_id)})
    if not old:
        raise HTTPException(status_code=404, detail="Periode tidak ditemukan")
    if status == "ACTIVE" and not old.get("is_test"):
        await db.periods.update_many({"status": "ACTIVE", "is_test": {"$ne": True}},
                                     {"$set": {"status": "COMPLETED"}})
    await db.periods.update_one({"_id": oid(item_id)}, {"$set": {"status": status, "updated_at": _now()}})
    await log_audit(user, "UPDATE", "PERIOD", "period", item_id,
                    {"status": old.get("status")}, {"status": status}, request)
    return {"message": f"Status periode diubah menjadi {status}"}


# =================== SCHOOLS ===================
@router.get("/schools", dependencies=[Depends(require_permission("SCHOOL_VIEW"))])
async def list_schools(request: Request, search: str = "", status: str = "",
                       page: int = 1, limit: int = 100, user: dict = Depends(get_current_user)):
    return await _list("schools", "SCHOOL", request, user, search, status, page, limit,
                       ["name", "code", "region"], scoped=True)


@router.get("/schools/{item_id}", dependencies=[Depends(require_permission("SCHOOL_VIEW"))])
async def get_school(item_id: str, user: dict = Depends(get_current_user)):
    doc = await db.schools.find_one({"_id": oid(item_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Sekolah tidak ditemukan")
    scope = user_school_scope(user)
    if scope is not None and item_id not in scope:
        raise HTTPException(status_code=403, detail="Data di luar cakupan Anda")
    return doc_out(doc)


@router.post("/schools", dependencies=[Depends(require_permission("SCHOOL_CREATE"))])
async def create_school(payload: SchoolIn, request: Request, user: dict = Depends(get_current_user)):
    return await _create("schools", "SCHOOL", "school", payload.model_dump(), user, request)


@router.put("/schools/{item_id}", dependencies=[Depends(require_permission("SCHOOL_UPDATE"))])
async def update_school(item_id: str, payload: SchoolIn, request: Request, user: dict = Depends(get_current_user)):
    return await _update("schools", "SCHOOL", "school", item_id, payload.model_dump(), user, request)


@router.delete("/schools/{item_id}", dependencies=[Depends(require_permission("SCHOOL_ARCHIVE"))])
async def archive_school(item_id: str, request: Request, user: dict = Depends(get_current_user)):
    return await _archive("schools", "SCHOOL", "school", item_id, user, request)


# =================== TEACHERS ===================
@router.get("/teachers", dependencies=[Depends(require_permission("TEACHER_VIEW"))])
async def list_teachers(request: Request, search: str = "", status: str = "",
                        page: int = 1, limit: int = 100, user: dict = Depends(get_current_user)):
    return await _list("teachers", "TEACHER", request, user, search, status, page, limit,
                       ["name", "phone"])


@router.get("/teachers/{item_id}", dependencies=[Depends(require_permission("TEACHER_VIEW"))])
async def get_teacher(item_id: str):
    doc = await db.teachers.find_one({"_id": oid(item_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Pengajar tidak ditemukan")
    return doc_out(doc)


@router.post("/teachers", dependencies=[Depends(require_permission("TEACHER_CREATE"))])
async def create_teacher(payload: TeacherIn, request: Request, user: dict = Depends(get_current_user)):
    return await _create("teachers", "TEACHER", "teacher", payload.model_dump(), user, request)


@router.put("/teachers/{item_id}", dependencies=[Depends(require_permission("TEACHER_UPDATE"))])
async def update_teacher(item_id: str, payload: TeacherIn, request: Request, user: dict = Depends(get_current_user)):
    return await _update("teachers", "TEACHER", "teacher", item_id, payload.model_dump(), user, request)


@router.delete("/teachers/{item_id}", dependencies=[Depends(require_permission("TEACHER_ARCHIVE"))])
async def archive_teacher(item_id: str, request: Request, user: dict = Depends(get_current_user)):
    return await _archive("teachers", "TEACHER", "teacher", item_id, user, request)


# =================== DEWAN HARIAN ===================
@router.get("/daily_board", dependencies=[Depends(require_permission("DH_VIEW"))])
async def list_dh(request: Request, search: str = "", status: str = "",
                  page: int = 1, limit: int = 100, user: dict = Depends(get_current_user)):
    return await _list("daily_board_members", "DH", request, user, search, status, page, limit,
                       ["name", "position"])


@router.get("/daily_board/{item_id}", dependencies=[Depends(require_permission("DH_VIEW"))])
async def get_dh(item_id: str):
    doc = await db.daily_board_members.find_one({"_id": oid(item_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Data tidak ditemukan")
    return doc_out(doc)


@router.post("/daily_board", dependencies=[Depends(require_permission("DH_CREATE"))])
async def create_dh(payload: DailyBoardIn, request: Request, user: dict = Depends(get_current_user)):
    return await _create("daily_board_members", "DH", "daily_board", payload.model_dump(), user, request)


@router.put("/daily_board/{item_id}", dependencies=[Depends(require_permission("DH_UPDATE"))])
async def update_dh(item_id: str, payload: DailyBoardIn, request: Request, user: dict = Depends(get_current_user)):
    return await _update("daily_board_members", "DH", "daily_board", item_id, payload.model_dump(), user, request)


@router.delete("/daily_board/{item_id}", dependencies=[Depends(require_permission("DH_ARCHIVE"))])
async def archive_dh(item_id: str, request: Request, user: dict = Depends(get_current_user)):
    return await _archive("daily_board_members", "DH", "daily_board", item_id, user, request)


# =================== OFFICERS ===================
@router.get("/officers", dependencies=[Depends(require_permission("OFFICER_VIEW"))])
async def list_officers(request: Request, search: str = "", status: str = "",
                        page: int = 1, limit: int = 100, user: dict = Depends(get_current_user)):
    return await _list("officers", "OFFICER", request, user, search, status, page, limit,
                       ["name", "position"])


@router.post("/officers", dependencies=[Depends(require_permission("OFFICER_CREATE"))])
async def create_officer(payload: OfficerIn, request: Request, user: dict = Depends(get_current_user)):
    return await _create("officers", "OFFICER", "officer", payload.model_dump(), user, request)


@router.put("/officers/{item_id}", dependencies=[Depends(require_permission("OFFICER_UPDATE"))])
async def update_officer(item_id: str, payload: OfficerIn, request: Request, user: dict = Depends(get_current_user)):
    return await _update("officers", "OFFICER", "officer", item_id, payload.model_dump(), user, request)


@router.delete("/officers/{item_id}", dependencies=[Depends(require_permission("OFFICER_ARCHIVE"))])
async def archive_officer(item_id: str, request: Request, user: dict = Depends(get_current_user)):
    return await _archive("officers", "OFFICER", "officer", item_id, user, request)


# =================== VEHICLES ===================
@router.get("/vehicles", dependencies=[Depends(require_permission("VEHICLE_VIEW"))])
async def list_vehicles(request: Request, search: str = "", status: str = "",
                        page: int = 1, limit: int = 100, user: dict = Depends(get_current_user)):
    return await _list("vehicles", "VEHICLE", request, user, search, status, page, limit,
                       ["code", "notes"])


@router.post("/vehicles", dependencies=[Depends(require_permission("VEHICLE_CREATE"))])
async def create_vehicle(payload: VehicleIn, request: Request, user: dict = Depends(get_current_user)):
    return await _create("vehicles", "VEHICLE", "vehicle", payload.model_dump(), user, request)


@router.put("/vehicles/{item_id}", dependencies=[Depends(require_permission("VEHICLE_UPDATE"))])
async def update_vehicle(item_id: str, payload: VehicleIn, request: Request, user: dict = Depends(get_current_user)):
    return await _update("vehicles", "VEHICLE", "vehicle", item_id, payload.model_dump(), user, request)


@router.delete("/vehicles/{item_id}", dependencies=[Depends(require_permission("VEHICLE_ARCHIVE"))])
async def archive_vehicle(item_id: str, request: Request, user: dict = Depends(get_current_user)):
    return await _archive("vehicles", "VEHICLE", "vehicle", item_id, user, request)
