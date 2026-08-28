ROLES = [
    "ADMIN",
    "KETUA_UMUM",
    "DEWAN_HARIAN",
    "KOORDINATOR",
    "PENGAJAR",
    "PENASEHAT_VIEWER",
]

ROLE_LABELS = {
    "ADMIN": "Admin",
    "KETUA_UMUM": "Ketua Umum",
    "DEWAN_HARIAN": "Dewan Harian",
    "KOORDINATOR": "Koordinator",
    "PENGAJAR": "Pengajar",
    "PENASEHAT_VIEWER": "Penasehat / Viewer",
}

# module -> actions
MODULES = {
    "PERIOD": ["VIEW", "CREATE", "UPDATE", "ARCHIVE", "MANAGE"],
    "SCHOOL": ["VIEW", "CREATE", "UPDATE", "ARCHIVE"],
    "TEACHER": ["VIEW", "CREATE", "UPDATE", "ARCHIVE"],
    "DH": ["VIEW", "CREATE", "UPDATE", "ARCHIVE"],
    "OFFICER": ["VIEW", "CREATE", "UPDATE", "ARCHIVE"],
    "VEHICLE": ["VIEW", "CREATE", "UPDATE", "ARCHIVE"],
    "ROSTER": ["VIEW", "UPLOAD", "IMPORT"],
    "ASSIGNMENT": ["VIEW", "CREATE", "UPDATE"],
    "SCHEDULE": ["VIEW", "CREATE", "UPDATE"],
    "DEPARTURE": ["VIEW", "CREATE", "UPDATE"],
    "PICKUP": ["VIEW", "CREATE", "UPDATE"],
    "ATTENDANCE": ["VIEW", "CREATE", "UPDATE"],
    "MONITORING": ["VIEW", "CREATE", "UPDATE", "REVIEW"],
    "DOCUMENTATION": ["VIEW", "UPLOAD"],
    "EVALUATION": ["VIEW", "CREATE", "UPDATE"],
    "REPORT": ["VIEW", "EXPORT"],
    "DASHBOARD": ["VIEW"],
    "USER": ["MANAGE"],
    "ROLE": ["MANAGE"],
    "AUDIT": ["VIEW"],
}


def all_permissions() -> list[str]:
    perms = []
    for mod, actions in MODULES.items():
        for a in actions:
            perms.append(f"{mod}_{a}")
    return perms


ALL_PERMS = all_permissions()

_VIEW_ALL = [p for p in ALL_PERMS if p.endswith("_VIEW")] + ["DASHBOARD_VIEW"]

ROLE_PERMISSIONS = {
    "ADMIN": set(ALL_PERMS),
    "KETUA_UMUM": set(_VIEW_ALL + ["REPORT_EXPORT", "AUDIT_VIEW", "MONITORING_REVIEW"]),
    "DEWAN_HARIAN": set(
        _VIEW_ALL + ["REPORT_EXPORT", "MONITORING_REVIEW"]
    ),
    "KOORDINATOR": set(
        [
            "DASHBOARD_VIEW",
            "SCHOOL_VIEW",
            "TEACHER_VIEW",
            "SCHEDULE_VIEW",
            "ASSIGNMENT_VIEW",
            "DEPARTURE_VIEW",
            "PICKUP_VIEW",
            "ATTENDANCE_VIEW",
            "ATTENDANCE_CREATE",
            "ATTENDANCE_UPDATE",
            "MONITORING_VIEW",
            "MONITORING_CREATE",
            "MONITORING_UPDATE",
            "DOCUMENTATION_VIEW",
            "DOCUMENTATION_UPLOAD",
            "REPORT_VIEW",
        ]
    ),
    "PENGAJAR": set(
        [
            "DASHBOARD_VIEW",
            "SCHEDULE_VIEW",
            "ASSIGNMENT_VIEW",
            "DEPARTURE_VIEW",
        ]
    ),
    "PENASEHAT_VIEWER": set(_VIEW_ALL + ["REPORT_EXPORT"]),
}

# Roles whose data is NOT restricted by school scope
UNSCOPED_ROLES = {"ADMIN", "KETUA_UMUM", "PENASEHAT_VIEWER"}


def permissions_for_role(role: str) -> list[str]:
    return sorted(ROLE_PERMISSIONS.get(role, set()))


def has_permission(role: str, perm: str) -> bool:
    return perm in ROLE_PERMISSIONS.get(role, set())
