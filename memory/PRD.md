# SIMPESRA LIM — Product Requirements & Progress

## Original Problem
SIMPESRA LIM (Sistem Informasi Monitoring Pesantren Ramadan — Lembaga Ittihadul Muballighin): a web app to manage & monitor a Ramadan Islamic education program. Delivered as a 10-package master specification. Goal for V1: "APK JADI DAN DAPAT DIGUNAKAN" — a stable, usable app with clear core workflows. UI in Bahasa Indonesia, responsive, RBAC + per-school data scope, multi-period (Hijri 1445/1446/1447), historical & testing data isolation, audit trail, dashboard with plan-vs-realization.

## Architecture
- Backend: FastAPI (modular: db, models, permissions, security, storage, audit, email_util, seed, routes_auth, routes_master, routes_admin, routes_dashboard, crud_base, server). MongoDB via Motor.
- Frontend: React (CRA + craco, `@/` alias), TailwindCSS, shadcn/ui, lucide-react, sonner, framer-motion, react-router, axios (withCredentials).
- Auth: JWT in httpOnly cookies (access 8h + refresh 7d), bcrypt hashing, login lockout, admin password reset via Emergent-managed email. Server-side authorization on every endpoint (require_permission) + per-school data scope + IDOR checks.
- Object storage: Emergent object store initialized at startup for future roster/documentation uploads (/api/files).

## User Personas & Roles
ADMIN (full), KETUA_UMUM (org-wide view), DEWAN_HARIAN (scoped view), KOORDINATOR (field ops, scoped write), PENGAJAR (self), PENASEHAT_VIEWER (read-only). Role = "what you can do"; Data Scope = "which schools' data".

## Core Requirements (static)
Master data (Periode, Sekolah, Pengajar, Dewan Harian, Petugas, Armada, User, Role/Permission); operational workflow (Roster→Penugasan→Jadwal→Pemberangkatan→Kehadiran→Monitoring→Dokumentasi→Evaluasi→Laporan); Dashboard (recap, Rencana Besok, Realisasi, Plan-vs-Realisasi, Perlu Perhatian, Ahad handling); Teacher evaluation with 1–5 star + indicators; Audit trail; multi-period isolation; testing-data separation.

## Implemented (2026-06 — Iteration 1: FOUNDATION)
- JWT auth: login/logout/me/refresh/forgot-password/reset-password; bcrypt; login lockout; audit on login/logout.
- RBAC: static permission matrix per role; server-side require_permission on all routes; per-school data scope + IDOR protection (verified by 24 pytest tests).
- Master Data CRUD (list/search/pagination/create/update/soft-archive): Periode (+status workflow, is_test flag, single-active enforcement), Sekolah (scoped), Pengajar, Dewan Harian (school_ids many-to-many), Petugas, Armada.
- User Management (create/update/deactivate, role + scope + school_ids, duplicate guard). Role & Permission matrix (read-only view). Audit Trail viewer.
- Dashboard: period context (Masehi + Hijri via Intl), master-data count cards, Realisasi/Rencana/Perlu Perhatian scaffolding with empty states, Ahad + Testing-mode banners, recent activity.
- Frontend: responsive layout (sidebar + drawer), role-based menu, login/forgot/reset pages, generic CrudPage, status badges, loading/empty/error states, toasts, confirmations.
- Seed: admin (pesantrenramadan07@gmail.com) + 5 demo role users + 1 TESTING period + 6 schools, 12 teachers, 3 vehicles, 4 DH, 2 officers.
- Tested: 24/24 backend pytest pass; frontend E2E critical flows pass (admin login, dashboard, master CRUD, koordinator RBAC).

## Backlog (prioritized)
### P0 — Operational modules (next iterations, per spec Phases 4–13)
- Roster upload → preview → validate → confirm → import (Excel, versioned) with object storage.
- Penugasan (assignment + history), Jadwal (schedule + calendar).
- Pemberangkatan (one vehicle → many schools/teachers, status workflow), Penjemputan.
- Kehadiran (status + absence reason + replacement teacher), Monitoring (draft/submitted/reviewed).
- Dokumentasi (file upload, scoped access).
- Dashboard live calculations: Rencana Besok, Realisasi, Plan-vs-Realisasi, Perlu Perhatian, drill-down detail.
### P1
- Evaluasi Program; Penilaian Pengajar (per-aspect 1–5 stars + indicator rubric snapshot).
- Laporan & Rekap (per school/teacher/vehicle/attendance/monitoring) + export (scoped).
- Historical comparison across periods.
### P2
- Notifications; editable role-permission management; report export formats.

## Next Tasks
1. Roster module (upload/validate/import + versioning) — unblocks assignment/schedule.
2. Schedule + Assignment (drives Rencana Besok).
3. Departure/Attendance (drives Realisasi + Plan-vs-Realisasi).

## Notes / Open Items
- Data TESTING (is_test periods) intentionally excluded from active/official dashboard & reports.
- Login lockout identifier = ip:email; concurrent tests from one IP can trip lockout (harness artifact only).
