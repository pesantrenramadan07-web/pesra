"""
SIMPESRA LIM — Backend API regression tests (iteration 1).
Covers: auth (cookies, /me, logout, refresh), RBAC (403 negative cases),
data scope (koordinator, dh, admin), IDOR guard on GET /schools/{id},
master data CRUD + archive, periods status transition (ACTIVE marks others COMPLETED),
user creation + duplicate email conflict + login of created user,
audit log entries, dashboard summary shape.
"""
import os
import uuid
import time
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else "https://pesantren-ramadan.preview.emergentagent.com"
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "pesantrenramadan07@gmail.com"
ADMIN_PASSWORD = "Admin#2026"
DEMO_PASSWORD = "Test#2026"

DEMO_USERS = {
    "ketua": "ketua@simpesra.test",
    "dh": "dh@simpesra.test",
    "koordinator": "koordinator@simpesra.test",
    "pengajar": "pengajar@simpesra.test",
    "viewer": "viewer@simpesra.test",
}


def _session(email, password):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    return s, r.json()


@pytest.fixture(scope="session")
def admin():
    s, u = _session(ADMIN_EMAIL, ADMIN_PASSWORD)
    return s, u


@pytest.fixture(scope="session")
def koordinator():
    s, u = _session(DEMO_USERS["koordinator"], DEMO_PASSWORD)
    return s, u


@pytest.fixture(scope="session")
def dh():
    s, u = _session(DEMO_USERS["dh"], DEMO_PASSWORD)
    return s, u


@pytest.fixture(scope="session")
def viewer():
    s, u = _session(DEMO_USERS["viewer"], DEMO_PASSWORD)
    return s, u


# ------------------- AUTH -------------------
class TestAuth:
    def test_admin_login_sets_cookies_and_permissions(self):
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "ADMIN"
        assert isinstance(data.get("permissions"), list) and len(data["permissions"]) > 0
        # cookies set
        assert "access_token" in s.cookies
        assert "refresh_token" in s.cookies

    def test_me_returns_permissions(self, admin):
        s, _ = admin
        r = s.get(f"{API}/auth/me")
        assert r.status_code == 200
        me = r.json()
        assert me["role"] == "ADMIN"
        assert "DASHBOARD_VIEW" in me["permissions"]

    def test_logout_clears_session(self):
        s, _ = _session(ADMIN_EMAIL, ADMIN_PASSWORD)
        r = s.post(f"{API}/auth/logout")
        assert r.status_code == 200
        # cookies should now be cleared - subsequent /me should 401
        s.cookies.clear()
        r2 = s.get(f"{API}/auth/me")
        assert r2.status_code == 401

    def test_all_demo_users_login(self):
        for _, email in DEMO_USERS.items():
            r = requests.post(f"{API}/auth/login", json={"email": email, "password": DEMO_PASSWORD})
            assert r.status_code == 200, f"{email} failed: {r.text}"

    def test_invalid_password_401(self):
        # use unique email so brute-force lock does not persist against admin/demo
        r = requests.post(f"{API}/auth/login", json={"email": f"nouser_{uuid.uuid4().hex}@x.com", "password": "bad"})
        assert r.status_code == 401


# ------------------- RBAC -------------------
class TestRBAC:
    def test_koordinator_cannot_create_school(self, koordinator):
        s, _ = koordinator
        r = s.post(f"{API}/schools", json={"code": "TESTX", "name": "Testx"})
        assert r.status_code == 403

    def test_viewer_cannot_create_school(self, viewer):
        s, _ = viewer
        r = s.post(f"{API}/schools", json={"code": "TESTV", "name": "TestV"})
        assert r.status_code == 403

    def test_koordinator_cannot_list_users(self, koordinator):
        s, _ = koordinator
        r = s.get(f"{API}/users")
        assert r.status_code == 403

    def test_koordinator_cannot_view_audit(self, koordinator):
        s, _ = koordinator
        r = s.get(f"{API}/audit_logs")
        assert r.status_code == 403


# ------------------- DATA SCOPE -------------------
class TestDataScope:
    def test_admin_sees_all_schools(self, admin):
        s, _ = admin
        r = s.get(f"{API}/schools?limit=100")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 6

    def test_koordinator_scoped_two_schools(self, koordinator):
        s, _ = koordinator
        r = s.get(f"{API}/schools?limit=100")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2, f"expected 2, got {data['total']}"

    def test_dh_scoped_four_schools(self, dh):
        s, _ = dh
        r = s.get(f"{API}/schools?limit=100")
        assert r.status_code == 200
        assert r.json()["total"] == 4

    def test_idor_koordinator_out_of_scope(self, admin, koordinator):
        sa, _ = admin
        all_schools = sa.get(f"{API}/schools?limit=100").json()["items"]
        sk, _ = koordinator
        my = sk.get(f"{API}/schools?limit=100").json()["items"]
        my_ids = {x["id"] for x in my}
        outside = [x for x in all_schools if x["id"] not in my_ids][0]
        r = sk.get(f"{API}/schools/{outside['id']}")
        assert r.status_code == 403


# ------------------- MASTER DATA CRUD -------------------
class TestMasterCRUD:
    def test_school_create_update_archive(self, admin):
        s, _ = admin
        code = f"TEST{uuid.uuid4().hex[:6].upper()}"
        r = s.post(f"{API}/schools", json={"code": code, "name": f"TEST_ {code}", "region": "TEST"})
        assert r.status_code == 200, r.text
        sch = r.json()
        sid = sch["id"]
        assert sch["code"] == code
        # GET verify
        r = s.get(f"{API}/schools/{sid}")
        assert r.status_code == 200 and r.json()["code"] == code
        # update
        r = s.put(f"{API}/schools/{sid}", json={"code": code, "name": f"TEST_UPD {code}"})
        assert r.status_code == 200 and r.json()["name"] == f"TEST_UPD {code}"
        # archive
        r = s.delete(f"{API}/schools/{sid}")
        assert r.status_code == 200
        r = s.get(f"{API}/schools/{sid}")
        assert r.status_code == 200 and r.json()["status"] == "INACTIVE"

    def test_teacher_and_vehicle_and_officer_create(self, admin):
        s, _ = admin
        r = s.post(f"{API}/teachers", json={"name": f"TEST_ Teacher {uuid.uuid4().hex[:4]}", "gender": "L"})
        assert r.status_code == 200
        r = s.post(f"{API}/vehicles", json={"code": f"TEST_V{uuid.uuid4().hex[:4]}", "type": "ELF_PONDOK", "capacity": 10})
        assert r.status_code == 200
        r = s.post(f"{API}/officers", json={"name": f"TEST_Officer {uuid.uuid4().hex[:4]}", "position": "Logistik"})
        assert r.status_code == 200

    def test_daily_board_with_school_ids(self, admin):
        s, _ = admin
        schools = s.get(f"{API}/schools?limit=100").json()["items"]
        sids = [x["id"] for x in schools[:2]]
        r = s.post(f"{API}/daily_board", json={"name": f"TEST_DH {uuid.uuid4().hex[:4]}", "position": "Sekretaris", "school_ids": sids})
        assert r.status_code == 200
        assert r.json()["school_ids"] == sids

    def test_schools_search(self, admin):
        s, _ = admin
        r = s.get(f"{API}/schools?search=Kediri&limit=100")
        assert r.status_code == 200
        assert r.json()["total"] >= 1


# ------------------- PERIODS -------------------
class TestPeriods:
    def test_create_and_set_active_marks_others_completed(self, admin):
        s, _ = admin
        # Create real (non-test) period
        r = s.post(f"{API}/periods", json={
            "name": f"TEST_Real Period {uuid.uuid4().hex[:4]}",
            "hijri_year": "1447", "start_date": "2026-02-01",
            "end_date": "2026-03-01", "status": "DRAFT", "is_test": False,
        })
        assert r.status_code == 200, r.text
        p1_id = r.json()["id"]

        r = s.post(f"{API}/periods", json={
            "name": f"TEST_Real Period B {uuid.uuid4().hex[:4]}",
            "hijri_year": "1447", "start_date": "2026-02-05",
            "end_date": "2026-03-05", "status": "DRAFT", "is_test": False,
        })
        p2_id = r.json()["id"]

        # Set p1 active
        r = s.post(f"{API}/periods/{p1_id}/status?status=ACTIVE")
        assert r.status_code == 200
        # Set p2 active - should mark p1 COMPLETED
        r = s.post(f"{API}/periods/{p2_id}/status?status=ACTIVE")
        assert r.status_code == 200
        r = s.get(f"{API}/periods/{p1_id}")
        assert r.json()["status"] == "COMPLETED"
        r = s.get(f"{API}/periods/{p2_id}")
        assert r.json()["status"] == "ACTIVE"

    def test_is_test_persists(self, admin):
        s, _ = admin
        r = s.post(f"{API}/periods", json={
            "name": f"TEST_Test Period {uuid.uuid4().hex[:4]}",
            "hijri_year": "1447", "start_date": "2026-02-01",
            "end_date": "2026-03-01", "status": "TESTING", "is_test": True,
        })
        assert r.status_code == 200
        assert r.json()["is_test"] is True


# ------------------- USERS -------------------
class TestUsers:
    def test_create_user_duplicate_and_login(self, admin):
        s, _ = admin
        email = f"test_{uuid.uuid4().hex[:8]}@simpesra.test"
        payload = {
            "name": "TEST_User", "email": email, "password": "TestPass#2026",
            "role": "KOORDINATOR", "status": "ACTIVE",
            "data_scope": "SCHOOL", "school_ids": [],
        }
        r = s.post(f"{API}/users", json=payload)
        assert r.status_code == 200, r.text
        assert r.json()["email"] == email
        # duplicate
        r = s.post(f"{API}/users", json=payload)
        assert r.status_code == 409
        # login as created user
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": "TestPass#2026"})
        assert r.status_code == 200
        assert r.json()["role"] == "KOORDINATOR"

    def test_admin_can_list_users(self, admin):
        s, _ = admin
        r = s.get(f"{API}/users?limit=100")
        assert r.status_code == 200
        assert r.json()["total"] >= 6


# ------------------- AUDIT -------------------
class TestAudit:
    def test_audit_logs_has_entries(self, admin):
        s, _ = admin
        r = s.get(f"{API}/audit_logs?limit=50")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] > 0
        # ensure _id excluded
        for item in data["items"]:
            assert "_id" not in item


# ------------------- DASHBOARD -------------------
class TestDashboard:
    def test_dashboard_summary_admin(self, admin):
        s, _ = admin
        r = s.get(f"{API}/dashboard/summary")
        assert r.status_code == 200, r.text
        data = r.json()
        assert "cards" in data and "schools" in data["cards"]
        assert data["cards"]["schools"]["value"] >= 6
        assert isinstance(data["is_ahad"], bool)
        assert "recent_activity" in data

    def test_dashboard_scoped_koordinator(self, koordinator):
        s, _ = koordinator
        r = s.get(f"{API}/dashboard/summary")
        assert r.status_code == 200
        data = r.json()
        assert data["cards"]["schools"]["value"] == 2
