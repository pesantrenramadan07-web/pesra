import os
import logging
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from fastapi import FastAPI, APIRouter, Depends, UploadFile, File, HTTPException, Request, Query, Response, Header
from starlette.middleware.cors import CORSMiddleware
import uuid

from db import db, client
from security import get_current_user, require_permission
from storage import init_storage, put_object, get_object, APP_NAME
from audit import log_audit
from crud_base import oid
from datetime import datetime, timezone

import routes_auth
import routes_master
import routes_dashboard
import routes_admin
import routes_roster
import routes_schedule
import seed

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("simpesra")

app = FastAPI(title="SIMPESRA LIM API")
api_router = APIRouter(prefix="/api")

ALLOWED_UPLOAD = {"jpg", "jpeg", "png", "webp", "pdf", "xlsx", "xls", "csv"}
MIME = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp",
        "pdf": "application/pdf", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel", "csv": "text/csv"}
MAX_SIZE = 15 * 1024 * 1024


@api_router.get("/")
async def root():
    return {"app": "SIMPESRA LIM", "status": "ok"}


@api_router.post("/files/upload", dependencies=[Depends(require_permission("DOCUMENTATION_UPLOAD"))])
async def upload_file(request: Request, file: UploadFile = File(...),
                      category: str = Query(default="documentation"),
                      user: dict = Depends(get_current_user)):
    ext = (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin").lower()
    if ext not in ALLOWED_UPLOAD:
        raise HTTPException(status_code=422, detail=f"Tipe file .{ext} tidak diizinkan")
    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=422, detail="Ukuran file melebihi 15MB")
    path = f"{APP_NAME}/{category}/{user['id']}/{uuid.uuid4()}.{ext}"
    ctype = MIME.get(ext, file.content_type or "application/octet-stream")
    result = put_object(path, data, ctype)
    rec = {
        "id": str(uuid.uuid4()), "storage_path": result["path"],
        "original_filename": file.filename, "content_type": ctype,
        "size": result.get("size", len(data)), "category": category,
        "uploaded_by": user["id"], "is_deleted": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.files.insert_one(rec)
    await log_audit(user, "UPLOAD", "DOCUMENTATION", "file", rec["id"], None,
                    {"filename": file.filename}, request)
    rec.pop("_id", None)
    return rec


@api_router.get("/files/{path:path}")
async def download_file(path: str, request: Request, auth: str = Query(default=None)):
    # Auth via cookie/header, or via ?auth= query token (for <img>/<a> tags)
    authed = False
    if request.cookies.get("access_token") or request.headers.get("Authorization"):
        await get_current_user(request)
        authed = True
    elif auth:
        from security import get_jwt_secret, JWT_ALGORITHM
        import jwt as _jwt
        try:
            claims = _jwt.decode(auth, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
            authed = claims.get("type") == "access"
        except Exception:
            authed = False
    if not authed:
        raise HTTPException(status_code=401, detail="Tidak terautentikasi")
    rec = await db.files.find_one({"storage_path": path, "is_deleted": False})
    if not rec:
        raise HTTPException(status_code=404, detail="File tidak ditemukan")
    content, ctype = get_object(path)
    return Response(content=content, media_type=rec.get("content_type", ctype))


api_router.include_router(routes_auth.router)
api_router.include_router(routes_master.router)
api_router.include_router(routes_dashboard.router)
api_router.include_router(routes_admin.router)
api_router.include_router(routes_roster.router)
api_router.include_router(routes_schedule.router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000"), "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    try:
        await seed.run_seed()
        logger.info("Seed completed")
    except Exception as e:
        logger.error(f"Seed failed: {e}")
    try:
        init_storage()
        logger.info("Storage initialized")
    except Exception as e:
        logger.error(f"Storage init failed: {e}")


@app.on_event("shutdown")
async def on_shutdown():
    client.close()
