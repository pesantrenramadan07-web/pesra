import os
from datetime import datetime, timezone

from db import db
from security import hash_password, verify_password
from permissions import ROLE_LABELS

TEST_PASSWORD = "Test#2026"


def _now():
    return datetime.now(timezone.utc).isoformat()


async def create_indexes():
    await db.users.create_index("email", unique=True)
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.password_reset_tokens.create_index("token_hash", unique=True)
    await db.login_attempts.create_index("email")
    await db.login_attempts.create_index("identifier")
    await db.password_reset_requests.create_index("email")
    await db.password_reset_requests.create_index("created_at", expireAfterSeconds=900)
    await db.audit_logs.create_index("timestamp")
    await db.schools.create_index("code")
    await db.periods.create_index("status")


async def seed_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "name": "Administrator", "email": admin_email,
            "password_hash": hash_password(admin_password), "role": "ADMIN",
            "status": "ACTIVE", "data_scope": "ALL", "school_ids": [],
            "token_version": 0, "created_at": _now(), "updated_at": _now(),
        })
    elif not verify_password(admin_password, existing.get("password_hash", "")):
        await db.users.update_one({"email": admin_email},
                                  {"$set": {"password_hash": hash_password(admin_password)}})


async def seed_demo():
    """Idempotent demo/test data. Only runs when no periods exist yet."""
    if await db.periods.count_documents({}) > 0:
        return

    period = {
        "name": "Pesantren Ramadan 1447 H (DEMO/TEST)", "hijri_year": "1447",
        "start_date": "2026-02-18", "end_date": "2026-03-19",
        "status": "TESTING", "is_test": True,
        "notes": "Data DEMO untuk uji coba workflow. Bukan data resmi.",
        "created_at": _now(), "updated_at": _now(),
    }
    await db.periods.insert_one(period)

    schools_data = [
        {"code": "SMAN1", "name": "SMAN 1 Kediri", "region": "Kota Kediri", "contact_person": "Pak Budi", "contact_phone": "0812000001"},
        {"code": "SMPN3", "name": "SMPN 3 Kediri", "region": "Kota Kediri", "contact_person": "Bu Sari", "contact_phone": "0812000002"},
        {"code": "MTSN2", "name": "MTsN 2 Kediri", "region": "Kab. Kediri", "contact_person": "Pak Anwar", "contact_phone": "0812000003"},
        {"code": "SMAN2", "name": "SMAN 2 Kediri", "region": "Kota Kediri", "contact_person": "Bu Rina", "contact_phone": "0812000004"},
        {"code": "SMKN1", "name": "SMKN 1 Kediri", "region": "Kab. Kediri", "contact_person": "Pak Hadi", "contact_phone": "0812000005"},
        {"code": "MAN1", "name": "MAN 1 Kediri", "region": "Kota Kediri", "contact_person": "Bu Laila", "contact_phone": "0812000006"},
    ]
    school_ids = []
    for s in schools_data:
        s.update({"address": s["region"], "status": "ACTIVE", "created_at": _now(), "updated_at": _now()})
        res = await db.schools.insert_one(s)
        school_ids.append(str(res.inserted_id))

    teachers = [
        ("Ahmad Fauzi", "L"), ("Muhammad Ali", "L"), ("Abdul Karim", "L"),
        ("Hasan Basri", "L"), ("Husein Umar", "L"), ("Siti Aminah", "P"),
        ("Fatimah Zahra", "P"), ("Umar Faruq", "L"), ("Zainab Sofia", "P"),
        ("Yusuf Mansur", "L"), ("Khadijah Nur", "P"), ("Ibrahim Malik", "L"),
    ]
    for i, (name, g) in enumerate(teachers):
        await db.teachers.insert_one({
            "name": name, "gender": g, "phone": f"08133300{i:02d}", "address": "Kediri",
            "status": "ACTIVE", "notes": "", "created_at": _now(), "updated_at": _now(),
        })

    vehicles = [
        {"code": "ELF PONDOK 01", "type": "ELF_PONDOK", "capacity": 12},
        {"code": "ELF PONDOK 02", "type": "ELF_PONDOK", "capacity": 12},
        {"code": "ELF LUAR 01", "type": "ELF_LUAR", "capacity": 10},
    ]
    for v in vehicles:
        v.update({"status": "ACTIVE", "notes": "", "created_at": _now(), "updated_at": _now()})
        await db.vehicles.insert_one(v)

    dh_members = [
        {"name": "KH. Abdullah", "position": "Ketua Umum", "school_ids": []},
        {"name": "Ust. Rahman", "position": "Ketua 1", "school_ids": school_ids[0:4]},
        {"name": "Ust. Fikri", "position": "Sekretaris Umum", "school_ids": school_ids[0:2]},
        {"name": "Ust. Hamid", "position": "Bendahara Umum", "school_ids": school_ids[4:6]},
    ]
    for d in dh_members:
        d.update({"phone": "", "status": "ACTIVE", "notes": "", "created_at": _now(), "updated_at": _now()})
        await db.daily_board_members.insert_one(d)

    officers = [
        {"name": "Sopir Joko", "position": "Petugas Armada"},
        {"name": "Petugas Doni", "position": "Logistik"},
    ]
    for o in officers:
        o.update({"phone": "", "status": "ACTIVE", "notes": "", "created_at": _now(), "updated_at": _now()})
        await db.officers.insert_one(o)

    # Demo users for each role
    demo_users = [
        ("Ketua Umum Demo", "ketua@simpesra.test", "KETUA_UMUM", "ALL", []),
        ("Dewan Harian Demo", "dh@simpesra.test", "DEWAN_HARIAN", "SCHOOL", school_ids[0:4]),
        ("Koordinator Demo", "koordinator@simpesra.test", "KOORDINATOR", "SCHOOL", school_ids[0:2]),
        ("Pengajar Demo", "pengajar@simpesra.test", "PENGAJAR", "SCHOOL", school_ids[0:1]),
        ("Penasehat Demo", "viewer@simpesra.test", "PENASEHAT_VIEWER", "ALL", []),
    ]
    for name, email, role, scope, sids in demo_users:
        if not await db.users.find_one({"email": email}):
            await db.users.insert_one({
                "name": name, "email": email, "password_hash": hash_password(TEST_PASSWORD),
                "role": role, "status": "ACTIVE", "data_scope": scope, "school_ids": sids,
                "token_version": 0, "created_at": _now(), "updated_at": _now(),
            })


async def write_test_credentials():
    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    content = f"""# Test Credentials — SIMPESRA LIM

## Admin (Owner)
- Email: {admin_email}
- Password: {admin_password}
- Role: ADMIN (full access)

## Demo Users (password: {TEST_PASSWORD})
- ketua@simpesra.test — KETUA_UMUM (semua sekolah, read-heavy)
- dh@simpesra.test — DEWAN_HARIAN (scope: 4 sekolah pertama)
- koordinator@simpesra.test — KOORDINATOR (scope: 2 sekolah pertama)
- pengajar@simpesra.test — PENGAJAR (scope: 1 sekolah)
- viewer@simpesra.test — PENASEHAT_VIEWER (read-only)

## Auth Endpoints
- POST /api/auth/login  (body: {{"email","password"}})
- POST /api/auth/logout
- GET  /api/auth/me
- POST /api/auth/refresh
- POST /api/auth/forgot-password
- POST /api/auth/reset-password

Auth uses httpOnly cookies (access_token, refresh_token). Frontend must send credentials: include / withCredentials: true.

## Notes
- Demo period is marked is_test=true (TESTING). It must NOT contaminate official/active reports.
- Master data (schools, teachers, vehicles, DH, officers) is seeded for the demo period.
"""
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write(content)


async def run_seed():
    await create_indexes()
    await seed_admin()
    await seed_demo()
    await write_test_credentials()
