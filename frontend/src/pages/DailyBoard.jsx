import React from "react";
import { useAuth } from "@/context/AuthContext";
import CrudPage from "@/components/CrudPage";
import StatusBadge from "@/components/StatusBadge";
import useSchoolOptions from "@/hooks/useSchoolOptions";
import { Users2 } from "lucide-react";

export default function DailyBoard() {
  const { can } = useAuth();
  const schoolOptions = useSchoolOptions();
  return (
    <CrudPage
      title="Master Dewan Harian" subtitle="Kelola Dewan Harian & sekolah tanggung jawab (bisa lebih dari satu)."
      icon={Users2} endpoint="/daily_board" entityName="Dewan Harian"
      searchPlaceholder="Cari nama / jabatan..."
      canCreate={can("DH_CREATE")} canEdit={can("DH_UPDATE")} canArchive={can("DH_ARCHIVE")}
      defaults={{ name: "", position: "", phone: "", status: "ACTIVE", notes: "", school_ids: [] }}
      columns={[
        { key: "name", label: "Nama" },
        { key: "position", label: "Jabatan" },
        { key: "school_ids", label: "Jml Sekolah", render: (r) => (r.school_ids || []).length },
        { key: "status", label: "Status", render: (r) => <StatusBadge value={r.status} /> },
      ]}
      formFields={[
        { name: "name", label: "Nama", required: true, colSpan: 1 },
        { name: "position", label: "Jabatan", required: true, colSpan: 1,
          placeholder: "Ketua Umum / Sekretaris 1 / ..." },
        { name: "phone", label: "Nomor HP", colSpan: 1 },
        { name: "status", label: "Status", type: "select", colSpan: 1, options: [
          { value: "ACTIVE", label: "Aktif" }, { value: "INACTIVE", label: "Nonaktif" }] },
        { name: "school_ids", label: "Sekolah Tanggung Jawab", type: "multiselect", options: schoolOptions },
        { name: "notes", label: "Catatan", type: "textarea" },
      ]}
    />
  );
}
