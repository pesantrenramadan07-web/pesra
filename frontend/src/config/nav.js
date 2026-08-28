import {
  LayoutDashboard, CalendarRange, School, GraduationCap, Users2, UserCog,
  Bus, Users, ShieldCheck, ScrollText, ClipboardList, Route, CalendarDays,
  Truck, CircleParking, UserCheck, ClipboardCheck, Images, FileBarChart2, Star,
} from "lucide-react";

// section: { label, items: [{ label, path, icon, perm, soon }] }
export const NAV = [
  {
    label: null,
    items: [{ label: "Dashboard", path: "/", icon: LayoutDashboard, perm: "DASHBOARD_VIEW" }],
  },
  {
    label: "Master Data",
    items: [
      { label: "Periode Program", path: "/periode", icon: CalendarRange, perm: "PERIOD_VIEW" },
      { label: "Sekolah", path: "/sekolah", icon: School, perm: "SCHOOL_VIEW" },
      { label: "Pengajar", path: "/pengajar", icon: GraduationCap, perm: "TEACHER_VIEW" },
      { label: "Dewan Harian", path: "/dewan-harian", icon: Users2, perm: "DH_VIEW" },
      { label: "Petugas", path: "/petugas", icon: UserCog, perm: "OFFICER_VIEW" },
      { label: "Armada", path: "/armada", icon: Bus, perm: "VEHICLE_VIEW" },
    ],
  },
  {
    label: "Kegiatan",
    items: [
      { label: "Roster", path: "/roster", icon: ClipboardList, perm: "ROSTER_VIEW" },
      { label: "Penugasan", path: "/penugasan", icon: Route, perm: "ASSIGNMENT_VIEW", soon: true },
      { label: "Jadwal", path: "/jadwal", icon: CalendarDays, perm: "SCHEDULE_VIEW", soon: true },
      { label: "Pemberangkatan", path: "/pemberangkatan", icon: Truck, perm: "DEPARTURE_VIEW", soon: true },
      { label: "Penjemputan", path: "/penjemputan", icon: CircleParking, perm: "PICKUP_VIEW", soon: true },
      { label: "Kehadiran", path: "/kehadiran", icon: UserCheck, perm: "ATTENDANCE_VIEW", soon: true },
      { label: "Monitoring", path: "/monitoring", icon: ClipboardCheck, perm: "MONITORING_VIEW", soon: true },
      { label: "Dokumentasi", path: "/dokumentasi", icon: Images, perm: "DOCUMENTATION_VIEW", soon: true },
    ],
  },
  {
    label: "Evaluasi",
    items: [
      { label: "Evaluasi Program", path: "/evaluasi-program", icon: FileBarChart2, perm: "EVALUATION_VIEW", soon: true },
      { label: "Penilaian Pengajar", path: "/penilaian-pengajar", icon: Star, perm: "EVALUATION_VIEW", soon: true },
    ],
  },
  {
    label: "Laporan",
    items: [
      { label: "Laporan & Rekap", path: "/laporan", icon: FileBarChart2, perm: "REPORT_VIEW", soon: true },
    ],
  },
  {
    label: "Administrasi",
    items: [
      { label: "Manajemen User", path: "/users", icon: Users, perm: "USER_MANAGE" },
      { label: "Role & Permission", path: "/roles", icon: ShieldCheck, perm: "ROLE_MANAGE" },
      { label: "Audit Trail", path: "/audit", icon: ScrollText, perm: "AUDIT_VIEW" },
    ],
  },
];
