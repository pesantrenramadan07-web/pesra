import os
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response, BackgroundTasks

from db import db
from models import LoginIn, ForgotPasswordIn, ResetPasswordIn
from security import (hash_password, verify_password, create_access_token,
                      create_refresh_token, set_auth_cookies, clear_auth_cookies,
                      get_current_user, get_jwt_secret, JWT_ALGORITHM)
from permissions import permissions_for_role, ROLE_LABELS
from audit import log_audit
from email_util import send_password_reset_email
import jwt
from bson import ObjectId

router = APIRouter(prefix="/auth")

MAX_ATTEMPTS = 5
LOCK_MINUTES = 15


def _user_public(user: dict) -> dict:
    return {
        "id": str(user.get("_id", user.get("id"))),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role"),
        "role_label": ROLE_LABELS.get(user.get("role"), user.get("role")),
        "status": user.get("status"),
        "data_scope": user.get("data_scope", "ALL"),
        "school_ids": user.get("school_ids", []),
        "permissions": permissions_for_role(user.get("role", "")),
    }


@router.post("/login")
async def login(payload: LoginIn, request: Request, response: Response):
    email = payload.email.strip().lower()
    ip = request.client.host if request.client else "unknown"
    identifier = f"{ip}:{email}"
    now = datetime.now(timezone.utc)

    attempt = await db.login_attempts.find_one({"identifier": identifier})
    if attempt and attempt.get("count", 0) >= MAX_ATTEMPTS:
        locked_until = attempt.get("locked_until")
        if locked_until and datetime.fromisoformat(locked_until) > now:
            raise HTTPException(status_code=429, detail="Terlalu banyak percobaan. Coba lagi nanti.")
        # lock window expired -> reset the counter
        await db.login_attempts.delete_many({"identifier": identifier})
        attempt = None

    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$inc": {"count": 1}, "$set": {"email": email, "identifier": identifier,
             "locked_until": (now + timedelta(minutes=LOCK_MINUTES)).isoformat()}},
            upsert=True,
        )
        raise HTTPException(status_code=401, detail="Username atau password tidak valid")

    if user.get("status") != "ACTIVE":
        raise HTTPException(status_code=403, detail="Akun nonaktif. Hubungi Admin.")

    await db.login_attempts.delete_many({"email": email})
    ver = user.get("token_version", 0)
    uid = str(user["_id"])
    set_auth_cookies(response, create_access_token(uid, email, ver), create_refresh_token(uid, ver))
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"last_login_at": now.isoformat()}})
    await log_audit(_user_public(user), "LOGIN", "AUTH", "user", uid, None, None, request)
    return _user_public(user)


@router.post("/logout")
async def logout(response: Response, request: Request, user: dict = Depends(get_current_user)):
    clear_auth_cookies(response)
    await log_audit(user, "LOGOUT", "AUTH", "user", user["id"], None, None, request)
    return {"message": "Berhasil keluar"}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    full = await db.users.find_one({"_id": ObjectId(user["id"])})
    return _user_public(full)


@router.post("/refresh")
async def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Tidak ada sesi")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token tidak valid")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user or payload.get("ver", 0) != user.get("token_version", 0):
            raise HTTPException(status_code=401, detail="Sesi berakhir")
        uid = str(user["_id"])
        set_auth_cookies(response, create_access_token(uid, user["email"], user.get("token_version", 0)),
                         create_refresh_token(uid, user.get("token_version", 0)))
        return _user_public(user)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token tidak valid")


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordIn, request: Request, background_tasks: BackgroundTasks):
    email = payload.email.strip().lower()
    now = datetime.now(timezone.utc)
    await db.password_reset_requests.insert_one({"email": email, "created_at": now.isoformat()})
    generic = {"message": "Jika email terdaftar, tautan reset telah dikirim."}
    recent = await db.password_reset_requests.count_documents(
        {"email": email, "created_at": {"$gt": (now - timedelta(minutes=15)).isoformat()}})
    if recent > 5:
        return generic
    user = await db.users.find_one({"email": email})
    if not user:
        return generic
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    await db.password_reset_tokens.insert_one({
        "token_hash": token_hash, "user_id": str(user["_id"]), "email": user["email"],
        "expires_at": (now + timedelta(hours=1)).isoformat(), "used": False,
        "created_at": now.isoformat(),
    })
    background_tasks.add_task(send_password_reset_email, user["email"], token)
    return generic


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordIn, request: Request):
    now = datetime.now(timezone.utc)
    h = hashlib.sha256(payload.token.encode()).hexdigest()
    doc = await db.password_reset_tokens.find_one_and_update(
        {"token_hash": h, "used": False, "expires_at": {"$gt": now.isoformat()}},
        {"$set": {"used": True}},
    )
    if not doc:
        raise HTTPException(status_code=400, detail="Tautan reset tidak valid atau sudah kadaluarsa")
    await db.users.update_one({"_id": ObjectId(doc["user_id"])},
                              {"$set": {"password_hash": hash_password(payload.password)},
                               "$inc": {"token_version": 1}})
    await db.password_reset_tokens.delete_many({"user_id": doc["user_id"], "used": False})
    await db.login_attempts.delete_many({"email": doc["email"]})
    return {"message": "Password berhasil diperbarui. Silakan masuk kembali."}
