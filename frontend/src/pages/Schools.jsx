import React from "react";
import { useAuth } from "@/context/AuthContext";
import CrudPage from "@/components/CrudPage";
import StatusBadge from "@/components/StatusBadge";
import { School } from "lucide-react";

export default function Schools() {
  const { can } = useAuth();
  return (
    <CrudPage
      title="Master Sekolah" subtitle="Kelola data sekolah peserta program"
      icon={School} endpoint="/schools" entityName="Sekolah"
      searchPlaceholder="Cari nama / kode / wilayah..."
      canCreate={can("SCHOOL_CREATE")} canEdit={can("SCHOOL_UPDATE")} canArchive={can("SCHOOL_ARCHIVE")}
      defaults={{ code: "", name: "", address: "", region: "", contact_person: "", contact_phone: "", status: "ACTIVE" }}
      columns={[
        { key: "code", label: "Kode" },
        { key: "name", label: "Nama Sekolah" },
        { key: "region", label: "Wilayah" },
        { key: "contact_person", label: "Kontak" },
        { key: "status", label: "Status", render: (r) => <StatusBadge value={r.status} /> },
      ]}
      formFields={[
        { name: "code", label: "Kode", required: true, colSpan: 1 },
        { name: "name", label: "Nama Sekolah", required: true, colSpan: 1 },
        { name: "region", label: "Wilayah", colSpan: 1 },
        { name: "contact_person", label: "Contact Person", colSpan: 1 },
        { name: "contact_phone", label: "Nomor Kontak", colSpan: 1 },
        { name: "status", label: "Status", type: "select", colSpan: 1, options: [
          { value: "ACTIVE", label: "Aktif" }, { value: "INACTIVE", label: "Nonaktif" }] },
        { name: "address", label: "Alamat", type: "textarea" },
      ]}
    />
  );
}
