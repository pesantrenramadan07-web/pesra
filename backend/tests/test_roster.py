"""
SIMPESRA LIM — Roster module pytest suite (iteration 2).
Covers:
- Template download (admin)
- Upload valid roster => status VALIDATED, stats, version increments, object storage
- Validation errors (unknown school, empty teacher, in-file duplicate) with Bahasa Indonesia messages
- Row status filtering
- No partial import (409 when stats.invalid > 0)
- Successful import => IMPORTED, imported_count, roster_details, auto-create teachers
- Re-import guard (409) and cancelled roster cannot be imported
- Cancel flow (only when not IMPORTED)
- Versioning/history preserved
- RBAC (koordinator/pengajar denied; admin allowed)
- Audit log entries for UPLOAD & IMPORT
"""
import io
import os
import uuid
import pytest
import requests
import openpyxl

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else "https://pesantren-ramadan.preview.emergentagent.com"
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "pesantrenramadan07@gmail.com"
ADMIN_PASSWORD = "Admin#2026"
DEMO_PASSWORD = "Test#2026"

COLUMNS = ["Sekolah", "Pengajar", "Jenis Kelamin", "No HP", "Posisi", "Koordinator", "Armada"]


def _login(email, password):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, f"Login failed {email}: {r.text}"
    return s


def _build_xlsx(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(COLUMNS)
    for r in rows:
        ws.append([r.get(c, "") for c in COLUMNS])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


@pytest.fixture(scope="module")
def admin():
    return _login(ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture(scope="module")
def koordinator():
    return _login("koordinator@simpesra.test", DEMO_PASSWORD)


@pytest.fixture(scope="module")
def pengajar():
    return _login("pengajar@simpesra.test", DEMO_PASSWORD)


@pytest.fixture(scope="module")
def active_period(admin):
    # Prefer an ACTIVE non-test period. Fallback: create one.
    r = admin.get(f"{API}/periods?limit=100")
    assert r.status_code == 200
    items = r.json().get("items", [])
    for p in items:
        if p.get("status") == "ACTIVE":
            return p
    # create one
    r = admin.post(f"{API}/periods", json={
        "name": f"TEST_Roster Period {uuid.uuid4().hex[:5]}",
        "hijri_year": "1447", "start_date": "2026-02-01",
        "end_date": "2026-03-01", "status": "DRAFT", "is_test": False,
    })
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    r2 = admin.post(f"{API}/periods/{pid}/status?status=ACTIVE")
    assert r2.status_code == 200
    return admin.get(f"{API}/periods/{pid}").json()


@pytest.fixture(scope="module")
def schools(admin):
    # Use the known seeded master schools (avoid TEST_-prefixed / possibly INACTIVE ones)
    known = {"SMAN 1 Kediri", "SMPN 3 Kediri", "MTsN 2 Kediri",
             "SMAN 2 Kediri", "SMKN 1 Kediri", "MAN 1 Kediri"}
    r = admin.get(f"{API}/schools?limit=100")
    assert r.status_code == 200
    items = [x for x in r.json()["items"]
             if x.get("status", "ACTIVE") == "ACTIVE" and x["name"] in known]
    assert len(items) >= 2, f"Not enough ACTIVE known schools: {items}"
    return items


# ---------------- TEMPLATE ----------------
class TestTemplate:
    def test_admin_can_download_template(self, admin):
        r = admin.get(f"{API}/rosters/template")
        assert r.status_code == 200
        assert "spreadsheetml" in r.headers.get("content-type", "")
        assert len(r.content) > 100
        # verify it's a valid xlsx with expected headers
        wb = openpyxl.load_workbook(io.BytesIO(r.content))
        ws = wb.active
        header = [c.value for c in next(ws.iter_rows(max_row=1))]
        for col in COLUMNS:
            assert col in header


# ---------------- UPLOAD + VALIDATE ----------------
class TestUploadValidate:
    def test_upload_valid_roster(self, admin, active_period, schools):
        s1 = schools[0]["name"]
        s2 = schools[1]["name"]
        data = _build_xlsx([
            {"Sekolah": s1, "Pengajar": f"TEST_Ustadz A {uuid.uuid4().hex[:4]}",
             "Jenis Kelamin": "L", "No HP": "081200000010", "Posisi": "Pengajar",
             "Koordinator": "Abdul Rahman", "Armada": "ELF PONDOK 01"},
            {"Sekolah": s2, "Pengajar": f"TEST_Ustadzah B {uuid.uuid4().hex[:4]}",
             "Jenis Kelamin": "P", "No HP": "081200000011", "Posisi": "Pengajar",
             "Koordinator": "Abdul Rahman", "Armada": "ELF PONDOK 01"},
        ])
        files = {"file": ("valid.xlsx", data,
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        r = admin.post(f"{API}/rosters/upload",
                       params={"period_id": active_period["id"]}, files=files)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "VALIDATED"
        assert d["stats"]["total"] == 2
        assert d["stats"]["valid"] == 2
        assert d["stats"]["invalid"] == 0
        assert d["stats"]["duplicate"] == 0
        assert d.get("storage_path"), "storage_path missing (object storage not used)"
        assert d.get("version", 0) >= 1
        pytest.roster_valid_id = d["id"]
        pytest.roster_valid_version = d["version"]

    def test_upload_with_errors_validation_messages(self, admin, active_period, schools):
        s1 = schools[0]["name"]
        dup_teacher = f"TEST_Dup {uuid.uuid4().hex[:4]}"
        data = _build_xlsx([
            {"Sekolah": "Sekolah Tidak Dikenal XYZ", "Pengajar": "Fulan"},  # unknown school
            {"Sekolah": s1, "Pengajar": ""},  # empty teacher
            {"Sekolah": s1, "Pengajar": dup_teacher},  # first occurrence -> VALID
            {"Sekolah": s1, "Pengajar": dup_teacher},  # duplicate in file
        ])
        files = {"file": ("errors.xlsx", data,
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        r = admin.post(f"{API}/rosters/upload",
                       params={"period_id": active_period["id"]}, files=files)
        assert r.status_code == 200, r.text
        d = r.json()
        stats = d["stats"]
        assert stats["total"] == 4
        assert stats["invalid"] == 2
        assert stats["duplicate"] == 1
        assert stats["valid"] == 1
        pytest.roster_bad_id = d["id"]

        # Filter rows by INVALID status
        r2 = admin.get(f"{API}/rosters/{d['id']}/rows?status=INVALID")
        assert r2.status_code == 200
        rows = r2.json()["items"]
        assert len(rows) == 2
        msgs = " | ".join(rw.get("validation_message", "") for rw in rows)
        # Bahasa Indonesia messages
        assert "tidak ditemukan" in msgs.lower() or "kosong" in msgs.lower()

        r3 = admin.get(f"{API}/rosters/{d['id']}/rows?status=DUPLICATE")
        assert r3.status_code == 200
        assert r3.json()["total"] == 1

        r4 = admin.get(f"{API}/rosters/{d['id']}/rows?status=VALID")
        assert r4.status_code == 200
        assert r4.json()["total"] == 1


# ---------------- IMPORT ----------------
class TestImport:
    def test_import_rejected_when_invalid_present(self, admin):
        rid = getattr(pytest, "roster_bad_id", None)
        assert rid, "prerequisite: upload with errors"
        r = admin.post(f"{API}/rosters/{rid}/import")
        assert r.status_code == 409
        detail = r.json().get("detail", "")
        assert "tidak valid" in detail.lower() or "ditolak" in detail.lower()

    def test_successful_import(self, admin):
        rid = getattr(pytest, "roster_valid_id", None)
        assert rid
        r = admin.post(f"{API}/rosters/{rid}/import")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["imported_count"] >= 1
        # roster now IMPORTED
        r2 = admin.get(f"{API}/rosters/{rid}")
        assert r2.status_code == 200
        assert r2.json()["status"] == "IMPORTED"
        # details endpoint returns imported rows
        r3 = admin.get(f"{API}/rosters/{rid}/details")
        assert r3.status_code == 200
        assert r3.json()["total"] == d["imported_count"]
        # teachers auto-created — verify names appear in teachers list
        # (search master pengajar)
        rt = admin.get(f"{API}/teachers?search=TEST_Ustadz&limit=50")
        assert rt.status_code == 200
        assert rt.json()["total"] >= 1

    def test_reimport_of_imported_roster_returns_409(self, admin):
        rid = getattr(pytest, "roster_valid_id", None)
        r = admin.post(f"{API}/rosters/{rid}/import")
        assert r.status_code == 409

    def test_cancelled_cannot_be_imported(self, admin, active_period, schools):
        # Upload an all-valid roster then cancel it, then attempt import
        data = _build_xlsx([
            {"Sekolah": schools[0]["name"],
             "Pengajar": f"TEST_ToCancel {uuid.uuid4().hex[:4]}"},
        ])
        files = {"file": ("cancelme.xlsx", data,
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        r = admin.post(f"{API}/rosters/upload",
                       params={"period_id": active_period["id"]}, files=files)
        assert r.status_code == 200
        rid = r.json()["id"]
        rc = admin.post(f"{API}/rosters/{rid}/cancel")
        assert rc.status_code == 200
        # verify status
        rg = admin.get(f"{API}/rosters/{rid}")
        assert rg.json()["status"] == "CANCELLED"
        # import should now 409
        ri = admin.post(f"{API}/rosters/{rid}/import")
        assert ri.status_code == 409

    def test_cancel_imported_forbidden(self, admin):
        rid = getattr(pytest, "roster_valid_id", None)
        r = admin.post(f"{API}/rosters/{rid}/cancel")
        assert r.status_code == 409


# ---------------- VERSIONING ----------------
class TestVersioning:
    def test_second_upload_creates_new_version_history_preserved(self, admin, active_period, schools):
        # count before
        r0 = admin.get(f"{API}/rosters?period_id={active_period['id']}&limit=100")
        before = r0.json()["total"]
        data = _build_xlsx([
            {"Sekolah": schools[0]["name"],
             "Pengajar": f"TEST_V2 {uuid.uuid4().hex[:4]}"},
        ])
        files = {"file": ("v2.xlsx", data,
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        r = admin.post(f"{API}/rosters/upload",
                       params={"period_id": active_period["id"]}, files=files)
        assert r.status_code == 200
        newv = r.json()["version"]
        assert newv == before + 1
        # list sorted newest first
        r2 = admin.get(f"{API}/rosters?period_id={active_period['id']}&limit=100")
        items = r2.json()["items"]
        assert items[0]["id"] == r.json()["id"]
        # previous roster still present (history preserved)
        assert r2.json()["total"] == before + 1


# ---------------- RBAC ----------------
class TestRosterRBAC:
    def test_koordinator_denied_list(self, koordinator):
        r = koordinator.get(f"{API}/rosters")
        assert r.status_code == 403

    def test_koordinator_denied_upload(self, koordinator, active_period, schools):
        data = _build_xlsx([{"Sekolah": schools[0]["name"], "Pengajar": "X"}])
        files = {"file": ("k.xlsx", data,
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        r = koordinator.post(f"{API}/rosters/upload",
                             params={"period_id": active_period["id"]}, files=files)
        assert r.status_code == 403

    def test_koordinator_denied_import(self, koordinator):
        rid = getattr(pytest, "roster_valid_id", None) or "000000000000000000000000"
        r = koordinator.post(f"{API}/rosters/{rid}/import")
        assert r.status_code == 403

    def test_pengajar_denied_list(self, pengajar):
        r = pengajar.get(f"{API}/rosters")
        assert r.status_code == 403


# ---------------- AUDIT ----------------
class TestRosterAudit:
    def test_audit_has_upload_and_import(self, admin):
        r = admin.get(f"{API}/audit_logs?limit=100")
        assert r.status_code == 200
        items = r.json()["items"]
        modules = [(x.get("action"), x.get("module")) for x in items]
        assert any(a == "UPLOAD" and m == "ROSTER" for a, m in modules), f"missing UPLOAD ROSTER audit: {modules[:10]}"
        assert any(a == "IMPORT" and m == "ROSTER" for a, m in modules), f"missing IMPORT ROSTER audit: {modules[:10]}"
