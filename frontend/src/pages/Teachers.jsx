import React from "react";
import { useAuth } from "@/context/AuthContext";
import CrudPage from "@/components/CrudPage";
import StatusBadge from "@/components/StatusBadge";
import { GraduationCap } from "lucide-react";

export default function Teachers() {
  const { can } = useAuth();
  return (
    <CrudPage
      title="Master Pengajar" subtitle="Kelola data pengajar"
      icon={GraduationCap} endpoint="/teachers" entityName="Pengajar"
      searchPlaceholder="Cari nama / nomor HP..."
      canCreate={can("TEACHER_CREATE")} canEdit={can("TEACHER_UPDATE")} canArchive={can("TEACHER_ARCHIVE")}
      defaults={{ name: "", gender: "L", phone: "", address: "", status: "ACTIVE", notes: "" }}
      columns={[
        { key: "name", label: "Nama" },
        { key: "gender", label: "Gender", render: (r) => (r.gender === "P" ? "Perempuan" : "Laki-laki") },
        { key: "phone", label: "Nomor HP" },
        { key: "status", label: "Status", render: (r) => <StatusBadge value={r.status} /> },
      ]}
      formFields={[
        { name: "name", label: "Nama", required: true },
        { name: "gender", label: "Jenis Kelamin", type: "select", colSpan: 1, options: [
          { value: "L", label: "Laki-laki" }, { value: "P", label: "Perempuan" }] },
        { name: "phone", label: "Nomor HP", colSpan: 1 },
        { name: "status", label: "Status", type: "select", colSpan: 1, options: [
          { value: "ACTIVE", label: "Aktif" }, { value: "INACTIVE", label: "Nonaktif" }] },
        { name: "address", label: "Alamat", colSpan: 1 },
        { name: "notes", label: "Catatan", type: "textarea" },
      ]}
    />
  );
}
