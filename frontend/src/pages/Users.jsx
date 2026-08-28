import React from "react";
import { useAuth } from "@/context/AuthContext";
import CrudPage from "@/components/CrudPage";
import StatusBadge from "@/components/StatusBadge";
import useSchoolOptions from "@/hooks/useSchoolOptions";
import { Users as UsersIcon } from "lucide-react";

const ROLE_OPTIONS = [
  { value: "ADMIN", label: "Admin" },
  { value: "KETUA_UMUM", label: "Ketua Umum" },
  { value: "DEWAN_HARIAN", label: "Dewan Harian" },
  { value: "KOORDINATOR", label: "Koordinator" },
  { value: "PENGAJAR", label: "Pengajar" },
  { value: "PENASEHAT_VIEWER", label: "Penasehat / Viewer" },
];

export default function Users() {
  const { can } = useAuth();
  const schoolOptions = useSchoolOptions();
  return (
    <CrudPage
      title="Manajemen User" subtitle="Kelola akun, role, dan cakupan data (scope) pengguna."
      icon={UsersIcon} endpoint="/users" entityName="User"
      searchPlaceholder="Cari nama / email..."
      canCreate={can("USER_MANAGE")} canEdit={can("USER_MANAGE")} canArchive={can("USER_MANAGE")}
      defaults={{ name: "", email: "", password: "", role: "PENGAJAR", status: "ACTIVE", data_scope: "ALL", school_ids: [] }}
      columns={[
        { key: "name", label: "Nama" },
        { key: "email", label: "Email" },
        { key: "role_label", label: "Role" },
        { key: "data_scope", label: "Scope", render: (r) => r.data_scope === "ALL" ? "Semua Data" : `${(r.school_ids || []).length} sekolah` },
        { key: "status", label: "Status", render: (r) => <StatusBadge value={r.status} /> },
      ]}
      formFields={[
        { name: "name", label: "Nama Lengkap", required: true, colSpan: 1 },
        { name: "email", label: "Email", required: true, colSpan: 1 },
        { name: "password", label: "Password", type: "password", colSpan: 1,
          hint: "Kosongkan saat mengubah bila tidak ingin mengganti." },
        { name: "role", label: "Role", type: "select", required: true, colSpan: 1, options: ROLE_OPTIONS },
        { name: "data_scope", label: "Cakupan Data", type: "select", colSpan: 1, options: [
          { value: "ALL", label: "Semua Data" }, { value: "SCHOOL", label: "Terbatas per Sekolah" }] },
        { name: "status", label: "Status", type: "select", colSpan: 1, options: [
          { value: "ACTIVE", label: "Aktif" }, { value: "INACTIVE", label: "Nonaktif" }] },
        { name: "school_ids", label: "Sekolah dalam Scope", type: "multiselect", options: schoolOptions,
          hint: "Berlaku bila Cakupan Data = Terbatas per Sekolah." },
      ]}
    />
  );
}
