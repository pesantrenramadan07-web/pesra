import React from "react";
import { useAuth } from "@/context/AuthContext";
import CrudPage from "@/components/CrudPage";
import StatusBadge from "@/components/StatusBadge";
import { UserCog } from "lucide-react";

export default function Officers() {
  const { can } = useAuth();
  return (
    <CrudPage
      title="Master Petugas" subtitle="Kelola data petugas operasional"
      icon={UserCog} endpoint="/officers" entityName="Petugas"
      searchPlaceholder="Cari nama / jabatan..."
      canCreate={can("OFFICER_CREATE")} canEdit={can("OFFICER_UPDATE")} canArchive={can("OFFICER_ARCHIVE")}
      defaults={{ name: "", position: "", phone: "", status: "ACTIVE", notes: "" }}
      columns={[
        { key: "name", label: "Nama" },
        { key: "position", label: "Jabatan" },
        { key: "phone", label: "Nomor HP" },
        { key: "status", label: "Status", render: (r) => <StatusBadge value={r.status} /> },
      ]}
      formFields={[
        { name: "name", label: "Nama", required: true, colSpan: 1 },
        { name: "position", label: "Jabatan", required: true, colSpan: 1 },
        { name: "phone", label: "Nomor HP", colSpan: 1 },
        { name: "status", label: "Status", type: "select", colSpan: 1, options: [
          { value: "ACTIVE", label: "Aktif" }, { value: "INACTIVE", label: "Nonaktif" }] },
        { name: "notes", label: "Catatan", type: "textarea" },
      ]}
    />
  );
}
