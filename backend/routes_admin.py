from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from bson import ObjectId

from db import db
from crud_base import doc_out, oid
from security import require_permission, get_current_user, hash_password
from permissions import ROLES, ROLE_LABELS, MODULES, ROLE_PERMISSIONS, permissions_for_role
from audit import log_audit
from models import UserIn

router = APIRouter()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _user_out(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    doc.pop("password_hash", None)
    doc.pop("token_version", None)
    doc["role_label"] = ROLE_LABELS.get(doc.get("role"), doc.get("role"))
    return doc


# =================== USERS ===================
@router.get("/users", dependencies=[Depends(require_permission("USER_MANAGE"))])
async def list_users(search: str = "", role: str = "", status: str = "",
                     page: int = 1, limit: int = 100):
    query: dict = {}
    if search:
        query["$or"] = [{"name": {"$regex": search, "$options": "i"}},
                        {"email": {"$regex": search, "$options": "i"}}]
    if role:
        query["role"] = role
    if status:
        query["status"] = status
    total = await db.users.count_documents(query)
    cursor = db.users.find(query).sort("created_at", -1).skip((page - 1) * limit).limit(min(limit, 200))
    items = [_user_out(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.post("/users", dependencies=[Depends(require_permission("USER_MANAGE"))])
async def create_user(payload: UserIn, request: Request, user: dict = Depends(get_current_user)):
    email = payload.email.strip().lower()
    if payload.role not in ROLES:
        raise HTTPException(status_code=422, detail="Role tidak valid")
    if not payload.password or len(payload.password) < 6:
        raise HTTPException(status_code=422, detail="Password minimal 6 karakter")
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="Email sudah terdaftar")
    doc = {
        "name": payload.name, "email": email, "password_hash": hash_password(payload.password),
        "role": payload.role, "status": payload.status,
        "data_scope": payload.data_scope, "school_ids": payload.school_ids,
        "token_version": 0, "created_at": _now(), "updated_at": _now(),
        "created_by": user["id"],
    }
    res = await db.users.insert_one(doc)
    await log_audit(user, "CREATE", "USER", "user", res.inserted_id, None,
                    {"email": email, "role": payload.role}, request)
    created = await db.users.find_one({"_id": res.inserted_id})
    return _user_out(created)


@router.put("/users/{user_id}", dependencies=[Depends(require_permission("USER_MANAGE"))])
async def update_user(user_id: str, payload: UserIn, request: Request, user: dict = Depends(get_current_user)):
    old = await db.users.find_one({"_id": oid(user_id)})
    if not old:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    if payload.role not in ROLES:
        raise HTTPException(status_code=422, detail="Role tidak valid")
    update = {
        "name": payload.name, "role": payload.role, "status": payload.status,
        "data_scope": payload.data_scope, "school_ids": payload.school_ids,
        "updated_at": _now(), "updated_by": user["id"],
    }
    if payload.password:
        if len(payload.password) < 6:
            raise HTTPException(status_code=422, detail="Password minimal 6 karakter")
        update["password_hash"] = hash_password(payload.password)
        update["token_version"] = old.get("token_version", 0) + 1
    await db.users.update_one({"_id": oid(user_id)}, {"$set": update})
    await log_audit(user, "UPDATE", "USER", "user", user_id,
                    {"role": old.get("role"), "status": old.get("status")},
                    {"role": payload.role, "status": payload.status}, request)
    updated = await db.users.find_one({"_id": oid(user_id)})
    return _user_out(updated)


@router.delete("/users/{user_id}", dependencies=[Depends(require_permission("USER_MANAGE"))])
async def deactivate_user(user_id: str, request: Request, user: dict = Depends(get_current_user)):
    old = await db.users.find_one({"_id": oid(user_id)})
    if not old:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    if str(old["_id"]) == user["id"]:
        raise HTTPException(status_code=400, detail="Tidak dapat menonaktifkan akun sendiri")
    await db.users.update_one({"_id": oid(user_id)},
                              {"$set": {"status": "INACTIVE", "updated_at": _now()},
                               "$inc": {"token_version": 1}})
    await log_audit(user, "ARCHIVE", "USER", "user", user_id, {"status": old.get("status")},
                    {"status": "INACTIVE"}, request)
    return {"message": "User dinonaktifkan"}


# =================== ROLES & PERMISSIONS ===================
@router.get("/roles", dependencies=[Depends(require_permission("ROLE_MANAGE"))])
async def list_roles():
    return [
        {"code": r, "label": ROLE_LABELS.get(r, r), "permissions": permissions_for_role(r)}
        for r in ROLES
    ]


@router.get("/permissions", dependencies=[Depends(require_permission("ROLE_MANAGE"))])
async def list_permissions():
    return {"modules": MODULES, "role_permissions": {r: permissions_for_role(r) for r in ROLES}}


# =================== AUDIT ===================
@router.get("/audit_logs", dependencies=[Depends(require_permission("AUDIT_VIEW"))])
async def list_audit(search: str = "", module: str = "", action: str = "",
                     page: int = 1, limit: int = 50):
    query: dict = {}
    if module:
        query["module"] = module
    if action:
        query["action"] = action
    if search:
        query["$or"] = [{"user_name": {"$regex": search, "$options": "i"}},
                        {"entity_type": {"$regex": search, "$options": "i"}}]
    total = await db.audit_logs.count_documents(query)
    cursor = db.audit_logs.find(query).sort("timestamp", -1).skip((page - 1) * limit).limit(min(limit, 200))
    items = [doc_out(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "limit": limit}
