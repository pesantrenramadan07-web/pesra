import io
import re
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Query, Response
from bson import ObjectId
import openpyxl

from db import db
from crud_base import doc_out, oid, is_oid
from security import require_permission, get_current_user, user_school_scope
from audit import log_audit
from storage import put_object, get_object
from permissions import UNSCOPED_ROLES, has_permission

router = APIRouter(prefix="/rosters")

APP_NS = "simpesra-lim"
COLUMNS = ["Sekolah", "Pengajar", "Jenis Kelamin", "No HP", "Posisi", "Koordinator", "Armada"]
ALLOWED_EXT = {"xlsx", "xls"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _norm(s):
    return (str(s).strip() if s is not None else "")


async def _parse_excel(data: bytes):
    try:
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception:
        raise HTTPException(status_code=422, detail="File Excel tidak valid atau rusak.")
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise HTTPException(status_code=422, detail="File Excel kosong.")
    header = [(_norm(h)).lower() for h in rows[0]]
    idx = {}
    for col in COLUMNS:
        try:
            idx[col] = header.index(col.lower())
        except ValueError:
            idx[col] = None
    if idx["Sekolah"] is None or idx["Pengajar"] is None:
        raise HTTPException(status_code=422,
            detail="Kolom wajib 'Sekolah' dan 'Pengajar' tidak ditemukan pada header.")
    parsed = []
    for i, r in enumerate(rows[1:], start=2):
        def g(col):
            j = idx[col]
            return _norm(r[j]) if (j is not None and j < len(r)) else ""
        raw = {c: g(c) for c in COLUMNS}
        if all(v == "" for v in raw.values()):
            continue  # skip blank lines
        parsed.append({"row_number": i, "raw": raw})
    return parsed


async def _validate_rows(period_id, parsed, user):
    schools = [doc_out(s) async for s in db.schools.find({"status": "ACTIVE"})]
    by_name = {s["name"].strip().lower(): s for s in schools}
    by_code = {(s.get("code") or "").strip().lower(): s for s in schools if s.get("code")}
    scope = user_school_scope(user)

    # existing imported (this period) school+teacher pairs for duplicate protection
    existing_pairs = set()
    async for d in db.roster_details.find({"period_id": period_id}):
        existing_pairs.add((d.get("school_id"), (d.get("teacher_name") or "").strip().lower()))

    seen = set()
    out = []
    stats = {"total": 0, "valid": 0, "invalid": 0, "duplicate": 0}
    for p in parsed:
        raw = p["raw"]
        school_key = raw["Sekolah"].strip().lower()
        teacher = raw["Pengajar"].strip()
        status = "VALID"
        msg = ""
        school = by_name.get(school_key) or by_code.get(school_key)
        school_id = school["id"] if school else None

        if not raw["Sekolah"]:
            status, msg = "INVALID", "Nama sekolah kosong"
        elif school is None:
            status, msg = "INVALID", f"Sekolah '{raw['Sekolah']}' tidak ditemukan di master"
        elif not teacher:
            status, msg = "INVALID", "Nama pengajar kosong"
        elif scope is not None and school_id not in scope:
            status, msg = "INVALID", "Sekolah di luar cakupan (scope) Anda"
        else:
            pair = (school_id, teacher.lower())
            if pair in seen:
                status, msg = "DUPLICATE", "Duplikat dalam file (sekolah + pengajar sama)"
            elif pair in existing_pairs:
                status, msg = "DUPLICATE", "Sudah ada pada roster periode ini"
            else:
                seen.add(pair)

        stats["total"] += 1
        stats[{"VALID": "valid", "INVALID": "invalid", "DUPLICATE": "duplicate"}[status]] += 1
        out.append({
            "row_number": p["row_number"], "raw_data": raw,
            "validation_status": status, "validation_message": msg,
            "school_id": school_id, "teacher_name": teacher,
        })
    return out, stats


def _strip_internal(doc, user):
    if doc and not has_permission(user.get("role", ""), "ROSTER_UPLOAD"):
        doc.pop("storage_path", None)
    return doc


# ============ LIST / DETAIL ============
@router.get("", dependencies=[Depends(require_permission("ROSTER_VIEW"))])
async def list_rosters(period_id: str = Query(default=None), page: int = 1, limit: int = 50,
                       user: dict = Depends(get_current_user)):
    query = {}
    if period_id and is_oid(period_id):
        query["period_id"] = period_id
    total = await db.rosters.count_documents(query)
    cursor = db.rosters.find(query).sort("uploaded_at", -1).skip((page - 1) * limit).limit(min(limit, 100))
    items = [_strip_internal(doc_out(d), user) async for d in cursor]
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.get("/template")
async def download_template(user: dict = Depends(require_permission("ROSTER_VIEW"))):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Roster"
    ws.append(COLUMNS)
    ws.append(["SMAN 1 Kediri", "Ahmad Fauzi", "L", "081200000001", "Pengajar", "Abdul Rahman", "ELF PONDOK 01"])
    ws.append(["SMPN 3 Kediri", "Siti Aminah", "P", "081200000002", "Pengajar", "Abdul Rahman", "ELF PONDOK 01"])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return Response(content=buf.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=template_roster.xlsx"})


@router.get("/{roster_id}", dependencies=[Depends(require_permission("ROSTER_VIEW"))])
async def get_roster(roster_id: str, user: dict = Depends(get_current_user)):
    doc = await db.rosters.find_one({"_id": oid(roster_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Roster tidak ditemukan")
    return _strip_internal(doc_out(doc), user)


@router.get("/{roster_id}/download")
async def download_original(roster_id: str, user: dict = Depends(require_permission("ROSTER_VIEW"))):
    doc = await db.rosters.find_one({"_id": oid(roster_id)})
    if not doc or not doc.get("storage_path"):
        raise HTTPException(status_code=404, detail="File roster tidak ditemukan")
    content, ctype = get_object(doc["storage_path"])
    fname = doc.get("original_filename") or "roster.xlsx"
    return Response(content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'})


@router.get("/{roster_id}/rows", dependencies=[Depends(require_permission("ROSTER_VIEW"))])
async def get_rows(roster_id: str, status: str = Query(default=""), page: int = 1, limit: int = 50):
    query = {"roster_id": roster_id}
    if status:
        query["validation_status"] = status
    total = await db.roster_rows.count_documents(query)
    cursor = db.roster_rows.find(query).sort("row_number", 1).skip((page - 1) * limit).limit(min(limit, 200))
    items = [doc_out(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "limit": limit}


# ============ UPLOAD (parse + validate + preview) ============
@router.post("/upload", dependencies=[Depends(require_permission("ROSTER_UPLOAD"))])
async def upload_roster(request: Request, file: UploadFile = File(...),
                        period_id: str = Query(...), notes: str = Query(default=""),
                        user: dict = Depends(get_current_user)):
    if not (period_id and is_oid(period_id)):
        raise HTTPException(status_code=422, detail="Periode tidak valid")
    period = await db.periods.find_one({"_id": ObjectId(period_id)})
    if not period:
        raise HTTPException(status_code=404, detail="Periode tidak ditemukan")

    ext = (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "").lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=422, detail="Hanya file Excel (.xlsx/.xls) yang diizinkan")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="Ukuran file melebihi 10MB")

    parsed = await _parse_excel(data)
    if not parsed:
        raise HTTPException(status_code=422, detail="Tidak ada baris data pada file.")
    rows, stats = await _validate_rows(period_id, parsed, user)

    # store file to object storage
    path = f"{APP_NS}/rosters/{period_id}/{uuid.uuid4()}.{ext}"
    ctype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    store = put_object(path, data, ctype)

    version = await db.rosters.count_documents({"period_id": period_id}) + 1
    roster_doc = {
        "period_id": period_id, "period_name": period.get("name"),
        "version": version, "original_filename": file.filename,
        "storage_path": store["path"], "file_size": store.get("size", len(data)),
        "status": "VALIDATED", "stats": stats, "notes": notes,
        "uploaded_by": user["id"], "uploaded_by_name": user["name"],
        "uploaded_at": _now(), "imported_at": None,
    }
    res = await db.rosters.insert_one(roster_doc)
    rid = str(res.inserted_id)
    for r in rows:
        r["roster_id"] = rid
    if rows:
        await db.roster_rows.insert_many(rows)
    await log_audit(user, "UPLOAD", "ROSTER", "roster", rid, None,
                    {"filename": file.filename, "version": version, "stats": stats}, request)
    out = doc_out(await db.rosters.find_one({"_id": res.inserted_id}))
    return out


# ============ IMPORT (no partial import if invalid) ============
@router.post("/{roster_id}/import", dependencies=[Depends(require_permission("ROSTER_IMPORT"))])
async def import_roster(roster_id: str, request: Request, user: dict = Depends(get_current_user)):
    roster = await db.rosters.find_one({"_id": oid(roster_id)})
    if not roster:
        raise HTTPException(status_code=404, detail="Roster tidak ditemukan")
    if roster["status"] == "IMPORTED":
        raise HTTPException(status_code=409, detail="Roster sudah diimpor sebelumnya")
    if roster["status"] == "CANCELLED":
        raise HTTPException(status_code=409, detail="Roster sudah dibatalkan")

    stats = roster.get("stats", {})
    if stats.get("invalid", 0) > 0:
        raise HTTPException(status_code=409,
            detail=f"Impor ditolak: masih ada {stats['invalid']} baris tidak valid. Perbaiki file lalu unggah ulang.")

    valid_rows = [r async for r in db.roster_rows.find(
        {"roster_id": roster_id, "validation_status": "VALID"})]
    if not valid_rows:
        raise HTTPException(status_code=409, detail="Tidak ada baris valid untuk diimpor")

    period_id = roster["period_id"]
    details = []
    for r in valid_rows:
        raw = r.get("raw_data", {})
        tname = r.get("teacher_name") or raw.get("Pengajar")
        # upsert teacher master by name (case-insensitive) — roster is the teacher source
        teacher = await db.teachers.find_one(
            {"name": {"$regex": f"^{re.escape(tname.strip())}$", "$options": "i"}})
        if not teacher:
            tdoc = {
                "name": tname, "gender": (raw.get("Jenis Kelamin") or "L")[:1].upper() if raw.get("Jenis Kelamin") else "L",
                "phone": raw.get("No HP") or "", "address": "", "status": "ACTIVE",
                "notes": "Dibuat otomatis dari import roster", "created_at": _now(), "updated_at": _now(),
                "created_by": user["id"],
            }
            tres = await db.teachers.insert_one(tdoc)
            teacher_id = str(tres.inserted_id)
        else:
            teacher_id = str(teacher["_id"])
        details.append({
            "period_id": period_id, "roster_id": roster_id, "roster_version": roster["version"],
            "school_id": r.get("school_id"), "teacher_id": teacher_id, "teacher_name": tname,
            "position": raw.get("Posisi") or "", "coordinator": raw.get("Koordinator") or "",
            "vehicle_hint": raw.get("Armada") or "", "raw_data": raw,
            "created_at": _now(),
        })
    if details:
        await db.roster_details.insert_many(details)

    await db.rosters.update_one({"_id": oid(roster_id)},
        {"$set": {"status": "IMPORTED", "imported_at": _now(),
                  "imported_count": len(details), "imported_by": user["id"]}})
    await log_audit(user, "IMPORT", "ROSTER", "roster", roster_id,
                    {"status": roster["status"]},
                    {"status": "IMPORTED", "imported_count": len(details)}, request)
    return {"message": f"{len(details)} baris berhasil diimpor.", "imported_count": len(details)}


# ============ CANCEL ============
@router.post("/{roster_id}/cancel", dependencies=[Depends(require_permission("ROSTER_UPLOAD"))])
async def cancel_roster(roster_id: str, request: Request, user: dict = Depends(get_current_user)):
    roster = await db.rosters.find_one({"_id": oid(roster_id)})
    if not roster:
        raise HTTPException(status_code=404, detail="Roster tidak ditemukan")
    if roster["status"] == "IMPORTED":
        raise HTTPException(status_code=409, detail="Roster yang sudah diimpor tidak dapat dibatalkan")
    await db.rosters.update_one({"_id": oid(roster_id)}, {"$set": {"status": "CANCELLED", "updated_at": _now()}})
    await log_audit(user, "UPDATE", "ROSTER", "roster", roster_id,
                    {"status": roster["status"]}, {"status": "CANCELLED"}, request)
    return {"message": "Roster dibatalkan."}


# ============ IMPORTED DETAILS (result) ============
@router.get("/{roster_id}/details", dependencies=[Depends(require_permission("ROSTER_VIEW"))])
async def get_details(roster_id: str, page: int = 1, limit: int = 50):
    query = {"roster_id": roster_id}
    total = await db.roster_details.count_documents(query)
    cursor = db.roster_details.find(query).skip((page - 1) * limit).limit(min(limit, 200))
    items = [doc_out(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "limit": limit}
