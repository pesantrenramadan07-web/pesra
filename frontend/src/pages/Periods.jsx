import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import api, { apiError } from "@/lib/api";
import { usePeriod } from "@/context/PeriodContext";
import { toast } from "sonner";
import CrudPage from "@/components/CrudPage";
import StatusBadge from "@/components/StatusBadge";
import { CalendarRange, Power } from "lucide-react";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { shortDate } from "@/lib/dates";

const STATUSES = ["DRAFT", "TESTING", "HISTORICAL", "ACTIVE", "COMPLETED", "ARCHIVED"];

export default function Periods() {
  const { can } = useAuth();
  const { reloadPeriods } = usePeriod();
  const [nonce, setNonce] = useState(0);

  const changeStatus = async (row, status, reload) => {
    try {
      await api.post(`/periods/${row.id}/status`, null, { params: { status } });
      toast.success(`Status periode diubah menjadi ${status}.`);
      reload(); reloadPeriods();
    } catch (e) {
      toast.error(apiError(e.response?.data?.detail) || "Gagal mengubah status.");
    }
  };

  return (
    <CrudPage
      key={nonce}
      title="Periode Program" subtitle="Kelola periode Pesantren Ramadan. Data antarperiode tidak tercampur."
      icon={CalendarRange} endpoint="/periods" entityName="Periode"
      searchPlaceholder="Cari nama / tahun hijriah..."
      canCreate={can("PERIOD_CREATE")} canEdit={can("PERIOD_UPDATE")} canArchive={false}
      defaults={{ name: "", hijri_year: "", start_date: "", end_date: "", status: "DRAFT", is_test: "false", notes: "" }}
      columns={[
        { key: "name", label: "Nama Periode" },
        { key: "hijri_year", label: "Tahun H" },
        { key: "start_date", label: "Mulai", render: (r) => shortDate(r.start_date) },
        { key: "end_date", label: "Selesai", render: (r) => shortDate(r.end_date) },
        { key: "is_test", label: "Jenis", render: (r) => r.is_test
          ? <StatusBadge value="TESTING" label="Testing" /> : <StatusBadge value="ACTIVE" label="Resmi" /> },
        { key: "status", label: "Status", render: (r) => <StatusBadge value={r.status} /> },
      ]}
      formFields={[
        { name: "name", label: "Nama Periode", required: true, placeholder: "Pesantren Ramadan 1447 H" },
        { name: "hijri_year", label: "Tahun Hijriah", required: true, colSpan: 1, placeholder: "1447" },
        { name: "status", label: "Status", type: "select", colSpan: 1, options: STATUSES.map((s) => ({ value: s, label: s })) },
        { name: "start_date", label: "Tanggal Mulai", type: "date", required: true, colSpan: 1 },
        { name: "end_date", label: "Tanggal Selesai", type: "date", required: true, colSpan: 1 },
        { name: "is_test", label: "Jenis Data", type: "select", options: [
          { value: "false", label: "Data Resmi (Official)" }, { value: "true", label: "Data Testing / Historis" }],
          hint: "Data Testing tidak akan memengaruhi dashboard & laporan resmi." },
        { name: "notes", label: "Catatan", type: "textarea" },
      ]}
      extraRowActions={can("PERIOD_MANAGE") ? (row, reload) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-500 hover:text-emerald-700" data-testid={`status-menu-${row.id}`}>
              <Power size={15} />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {STATUSES.map((s) => (
              <DropdownMenuItem key={s} onClick={() => changeStatus(row, s, reload)} data-testid={`set-status-${s}`}>
                Set {s}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      ) : null}
    />
  );
}
