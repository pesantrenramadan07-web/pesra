import React from "react";
import { useAuth } from "@/context/AuthContext";
import CrudPage from "@/components/CrudPage";
import StatusBadge from "@/components/StatusBadge";
import { Bus } from "lucide-react";

export default function Vehicles() {
  const { can } = useAuth();
  return (
    <CrudPage
      title="Master Armada" subtitle="Kelola data armada. Satu armada dapat membawa beberapa sekolah."
      icon={Bus} endpoint="/vehicles" entityName="Armada"
      searchPlaceholder="Cari kode armada..."
      canCreate={can("VEHICLE_CREATE")} canEdit={can("VEHICLE_UPDATE")} canArchive={can("VEHICLE_ARCHIVE")}
      defaults={{ code: "", type: "ELF_PONDOK", capacity: 0, status: "ACTIVE", notes: "" }}
      columns={[
        { key: "code", label: "Kode" },
        { key: "type", label: "Jenis", render: (r) => (r.type === "ELF_LUAR" ? "Elf Luar" : "Elf Pondok") },
        { key: "capacity", label: "Kapasitas" },
        { key: "status", label: "Status", render: (r) => <StatusBadge value={r.status} /> },
      ]}
      formFields={[
        { name: "code", label: "Kode / Nama Armada", required: true, colSpan: 1 },
        { name: "type", label: "Jenis", type: "select", colSpan: 1, options: [
          { value: "ELF_PONDOK", label: "Elf Pondok" }, { value: "ELF_LUAR", label: "Elf Luar" }] },
        { name: "capacity", label: "Kapasitas", type: "number", colSpan: 1 },
        { name: "status", label: "Status", type: "select", colSpan: 1, options: [
          { value: "ACTIVE", label: "Aktif" }, { value: "INACTIVE", label: "Nonaktif" }] },
        { name: "notes", label: "Catatan", type: "textarea" },
      ]}
    />
  );
}
