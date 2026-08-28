# SIMPESRA LIM — Auth & RBAC Testing Notes

Auth uses JWT in httpOnly cookies (access_token 8h, refresh_token 7d).
Frontend uses axios withCredentials. Backend base: internal http://localhost:8001, external via REACT_APP_BACKEND_URL.

## Accounts (see /app/memory/test_credentials.md)
- Admin: pesantrenramadan07@gmail.com / Admin#2026  (role ADMIN, full access)
- ketua@simpesra.test / Test#2026 (KETUA_UMUM)
- dh@simpesra.test / Test#2026 (DEWAN_HARIAN, scope = 4 schools)
- koordinator@simpesra.test / Test#2026 (KOORDINATOR, scope = 2 schools)
- pengajar@simpesra.test / Test#2026 (PENGAJAR)
- viewer@simpesra.test / Test#2026 (PENASEHAT_VIEWER, read-only)

## Endpoints
- POST /api/auth/login {email,password} -> sets cookies, returns user with permissions[]
- POST /api/auth/logout
- GET  /api/auth/me
- POST /api/auth/refresh
- POST /api/auth/forgot-password / POST /api/auth/reset-password
- Master: /api/periods, /api/schools, /api/teachers, /api/daily_board, /api/officers, /api/vehicles
- Admin: /api/users, /api/roles, /api/permissions, /api/audit_logs
- /api/dashboard/summary

## RBAC expectations
- KOORDINATOR must NOT create schools (expect 403 on POST /api/schools).
- KOORDINATOR GET /api/schools returns ONLY its scoped schools (2). Admin returns all (6).
- PENASEHAT_VIEWER cannot create/update anything (403 on writes).
- Non-admin cannot access /api/users (403).
- Period status: setting one non-test period ACTIVE marks others COMPLETED.

## Password reset local test
To read the reset link locally, set FRONTEND_URL="http://localhost:3000" in backend/.env,
restart backend; link is logged to backend log. Restore https origin afterwards.
