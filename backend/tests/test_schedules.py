"""
SIMPESRA LIM — Schedule module tests (iteration 3).
Covers: CRUD, duplicate protection, status workflow transitions, schedule_history,
data scope for KOORDINATOR, RBAC negative cases, audit logs, dashboard schedule-driven values.
"""
import os
import uuid
import pytest
import requests
from datetime import date, timedelta

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "pesantrenramadan07@gmail.com"
ADMIN_PASSWORD = "Admin#2026"
DEMO_PASSWORD = "Test#2026"


def _session(email, password):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    return s, r.json()


@pytest.fixture(scope="module")
def admin():
    return _session(ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture(scope="module")
def koordinator():
    return _session("koordinator@simpesra.test", DEMO_PASSWORD)


@pytest.fixture(scope="module")
def viewer():
    return _session("viewer@simpesra.test", DEMO_PASSWORD)


@pytest.fixture(scope="module")
def demo_period(admin):
    s, _ = admin
    r = s.get(f"{API}/periods?limit=50")
    assert r.status_code == 200
    # Find is_test period (demo/test period seeded)
    for p in r.json()["items"]:
        if p.get("is_test"):
            return p
    # fallback: any period
    return r.json()["items"][0]


@pytest.fixture(scope="module")
def demo_schools(admin):
    s, _ = admin
    r = s.get(f"{API}/schools?limit=100")
    assert r.status_code == 200
    return r.json()["items"]


def _unique_future_date(offset_days_start=5):
    # Use a date well beyond seed's today/tomorrow to avoid duplicate collisions
    return (date.today() + timedelta(days=offset_days_start + int(uuid.uuid4().int % 90))).isoformat()


# ------------------- CRUD -------------------
class TestScheduleCRUD:
    def test_admin_create_schedule(self, admin, demo_period, demo_schools):
        s, _ = admin
        payload = {
            "period_id": demo_period["id"], "school_id": demo_schools[2]["id"],
            "date": _unique_future_date(30), "start_time": "07:00", "end_time": "12:00",
            "status": "PLANNED", "notes": "TEST_create",
        }
        r = s.post(f"{API}/schedules", json=payload)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["school_name"] == demo_schools[2]["name"]
        assert d["period_name"] == demo_period["name"]
        assert d["status"] == "PLANNED"
        assert "_id" not in d
        # GET verify
        rg = s.get(f"{API}/schedules/{d['id']}")
        assert rg.status_code == 200
        assert rg.json()["date"] == payload["date"]

    def test_list_with_filters(self, admin, demo_period):
        s, _ = admin
        r = s.get(f"{API}/schedules", params={"period_id": demo_period["id"], "limit": 100})
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 5  # seed created 3 today + 4 tomorrow
        # status filter
        r2 = s.get(f"{API}/schedules", params={"period_id": demo_period["id"], "status": "PLANNED", "limit": 100})
        assert r2.status_code == 200
        for it in r2.json()["items"]:
            assert it["status"] == "PLANNED"

    def test_update_period_immutable(self, admin, demo_period, demo_schools):
        s, _ = admin
        d = _unique_future_date(60)
        create = s.post(f"{API}/schedules", json={
            "period_id": demo_period["id"], "school_id": demo_schools[3]["id"],
            "date": d, "start_time": "08:00", "end_time": "11:00",
            "status": "PLANNED", "notes": "TEST_upd",
        })
        assert create.status_code == 200, create.text
        sid = create.json()["id"]
        # try to change period_id — should be ignored (period cannot change)
        fake_pid = "507f1f77bcf86cd799439011"
        upd = s.put(f"{API}/schedules/{sid}", json={
            "period_id": fake_pid, "school_id": demo_schools[3]["id"],
            "date": d, "start_time": "08:30", "end_time": "11:30",
            "status": "PLANNED", "notes": "TEST_upd2",
        })
        assert upd.status_code == 200, upd.text
        assert upd.json()["period_id"] == demo_period["id"]
        assert upd.json()["start_time"] == "08:30"

    def test_delete_marks_cancelled(self, admin, demo_period, demo_schools):
        s, _ = admin
        d = _unique_future_date(90)
        r = s.post(f"{API}/schedules", json={
            "period_id": demo_period["id"], "school_id": demo_schools[4]["id"],
            "date": d, "start_time": "07:00", "end_time": "12:00",
            "status": "PLANNED", "notes": "TEST_del",
        })
        sid = r.json()["id"]
        rd = s.delete(f"{API}/schedules/{sid}")
        assert rd.status_code == 200
        rg = s.get(f"{API}/schedules/{sid}")
        assert rg.status_code == 200
        assert rg.json()["status"] == "CANCELLED"

    def test_duplicate_protection(self, admin, demo_period, demo_schools):
        s, _ = admin
        d = _unique_future_date(120)
        payload = {
            "period_id": demo_period["id"], "school_id": demo_schools[5]["id"],
            "date": d, "start_time": "07:00", "end_time": "12:00",
            "status": "PLANNED", "notes": "TEST_dup",
        }
        r1 = s.post(f"{API}/schedules", json=payload)
        assert r1.status_code == 200, r1.text
        r2 = s.post(f"{API}/schedules", json=payload)
        assert r2.status_code == 409


# ------------------- STATUS WORKFLOW -------------------
class TestStatusWorkflow:
    @pytest.fixture
    def new_schedule(self, admin, demo_period, demo_schools):
        s, _ = admin
        d = _unique_future_date(150)
        r = s.post(f"{API}/schedules", json={
            "period_id": demo_period["id"], "school_id": demo_schools[2]["id"],
            "date": d, "start_time": "07:00", "end_time": "12:00",
            "status": "PLANNED", "notes": "TEST_flow",
        })
        assert r.status_code == 200, r.text
        return s, r.json()["id"]

    def test_planned_to_completed_rejected(self, new_schedule):
        s, sid = new_schedule
        r = s.post(f"{API}/schedules/{sid}/status", params={"status": "COMPLETED"})
        assert r.status_code == 409

    def test_full_workflow_and_history(self, new_schedule):
        s, sid = new_schedule
        # PLANNED -> CONFIRMED
        r = s.post(f"{API}/schedules/{sid}/status", params={"status": "CONFIRMED"})
        assert r.status_code == 200, r.text
        # CONFIRMED -> ONGOING
        r = s.post(f"{API}/schedules/{sid}/status", params={"status": "ONGOING"})
        assert r.status_code == 200
        # ONGOING -> COMPLETED
        r = s.post(f"{API}/schedules/{sid}/status", params={"status": "COMPLETED"})
        assert r.status_code == 200
        # COMPLETED terminal — can't move to CONFIRMED
        r = s.post(f"{API}/schedules/{sid}/status", params={"status": "CONFIRMED"})
        assert r.status_code == 409
        # history
        rh = s.get(f"{API}/schedules/{sid}/history")
        assert rh.status_code == 200
        entries = rh.json()
        status_transitions = [e for e in entries if e.get("change_type") == "STATUS"]
        assert len(status_transitions) >= 3
        for e in entries:
            assert "_id" not in e


# ------------------- DATA SCOPE -------------------
class TestDataScope:
    def test_koordinator_only_sees_scoped(self, koordinator, demo_period):
        s, _ = koordinator
        r = s.get(f"{API}/schedules", params={"period_id": demo_period["id"], "limit": 100})
        assert r.status_code == 200
        # koordinator scope = 2 schools (indices 0..1). Seed created today for schools 0..2 and tomorrow for 0..3.
        items = r.json()["items"]
        # school_ids should be within koordinator's scope (2 schools)
        distinct_schools = {it["school_id"] for it in items}
        assert len(distinct_schools) <= 2

    def test_koordinator_get_out_of_scope_403(self, admin, koordinator, demo_period, demo_schools):
        sa, _ = admin
        # find a schedule in an out-of-scope school (schools[3+] are out of koord scope)
        r = sa.get(f"{API}/schedules", params={"period_id": demo_period["id"], "school_id": demo_schools[3]["id"], "limit": 5})
        items = r.json().get("items", [])
        if not items:
            # create one
            create = sa.post(f"{API}/schedules", json={
                "period_id": demo_period["id"], "school_id": demo_schools[3]["id"],
                "date": _unique_future_date(200), "start_time": "07:00", "end_time": "12:00",
                "status": "PLANNED", "notes": "TEST_oos",
            })
            assert create.status_code == 200
            sid = create.json()["id"]
        else:
            sid = items[0]["id"]
        sk, _ = koordinator
        r = sk.get(f"{API}/schedules/{sid}")
        assert r.status_code == 403

    def test_koordinator_cannot_create(self, koordinator, demo_period, demo_schools):
        s, _ = koordinator
        r = s.post(f"{API}/schedules", json={
            "period_id": demo_period["id"], "school_id": demo_schools[0]["id"],
            "date": _unique_future_date(220), "start_time": "07:00", "end_time": "12:00",
            "status": "PLANNED",
        })
        assert r.status_code == 403

    def test_koordinator_cannot_update(self, admin, koordinator, demo_period, demo_schools):
        sa, _ = admin
        # Find or create schedule in koordinator scope (school 0)
        r = sa.get(f"{API}/schedules", params={"period_id": demo_period["id"], "school_id": demo_schools[0]["id"], "limit": 5})
        items = r.json().get("items", [])
        assert items, "expected a seed schedule for school 0"
        sid = items[0]["id"]
        sk, _ = koordinator
        r = sk.post(f"{API}/schedules/{sid}/status", params={"status": "CONFIRMED"})
        assert r.status_code == 403


# ------------------- AUDIT -------------------
class TestAudit:
    def test_audit_has_schedule_entries(self, admin):
        s, _ = admin
        r = s.get(f"{API}/audit_logs", params={"limit": 200})
        assert r.status_code == 200
        modules = {it.get("module") for it in r.json()["items"]}
        assert "SCHEDULE" in modules


# ------------------- DASHBOARD SCHEDULE-DRIVEN -------------------
class TestDashboardScheduleDriven:
    def test_summary_uses_schedule_data(self, admin, demo_period):
        s, _ = admin
        r = s.get(f"{API}/dashboard/summary", params={"period_id": demo_period["id"]})
        assert r.status_code == 200, r.text
        data = r.json()
        # rencana_besok should have items from seed (4 tomorrow)
        assert data["rencana_besok"]["available"] is True
        assert data["rencana_besok"]["schools"] >= 1
        assert isinstance(data["rencana_besok"]["items"], list)
        assert len(data["rencana_besok"]["items"]) == data["rencana_besok"]["schools"]
        # realisasi from today's schedules
        assert data["realisasi"]["schools_total"] >= 1
        assert data["realisasi"]["schools_started"] >= 1  # seed: 2 ONGOING today
        # plan_vs_realization has Sekolah row
        labels = {row["label"] for row in data["plan_vs_realization"]}
        assert "Sekolah" in labels

    def test_status_change_affects_realisasi(self, admin, demo_period, demo_schools):
        s, _ = admin
        # Find a today+PLANNED schedule via seed (school[2] was CONFIRMED today per seed)
        today = date.today().isoformat()
        r = s.get(f"{API}/schedules", params={"period_id": demo_period["id"], "date": today, "limit": 100})
        items = r.json()["items"]
        confirmed = [x for x in items if x["status"] == "CONFIRMED"]
        if not confirmed:
            pytest.skip("no CONFIRMED today schedule to promote")
        sid = confirmed[0]["id"]
        # baseline
        base = s.get(f"{API}/dashboard/summary", params={"period_id": demo_period["id"]}).json()
        started_before = base["realisasi"]["schools_started"]
        # promote to ONGOING
        r = s.post(f"{API}/schedules/{sid}/status", params={"status": "ONGOING"})
        assert r.status_code == 200, r.text
        after = s.get(f"{API}/dashboard/summary", params={"period_id": demo_period["id"]}).json()
        assert after["realisasi"]["schools_started"] == started_before + 1
