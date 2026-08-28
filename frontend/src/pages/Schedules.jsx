import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { usePeriod } from "@/context/PeriodContext";
import api, { apiError } from "@/lib/api";
import { toast } from "sonner";
import CrudPage from "@/components/CrudPage";
import StatusBadge from "@/components/StatusBadge";
import useSchoolOptions from "@/hooks/useSchoolOptions";
import { CalendarDays, Power } from "lucide-react";
import { Button } from "@/components/ui/button";
import { shortDate } from "@/lib/dates";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const STATUSES = ["PLANNED", "CONFIRMED", "ONGOING", "COMPLETED", "CANCELLED"];

export default function Schedules() {
  const { can } = useAuth();
  const { activePeriod } = usePeriod();
  const schoolOptions = useSchoolOptions();

  const changeStatus = async (row, status, reload) => {
    try {
      await api.post(`/schedules/${row.id}/status`, null, { params: { status } });
      toast.success(`Status jadwal diubah menjadi ${status}.`);
      reload();
    } catch (e) {
      toast.error(apiError(e.response?.data?.detail) || "Gagal mengubah status.");
    }
  };

  if (!activePeriod) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 text-amber-800 text-sm" data-testid="no-period-warning">
        Belum ada periode dipilih. Pilih periode pada header terlebih dahulu untuk mengelola jadwal.
      </div>
    );
  }

  return (
    <CrudPage
      title="Jadwal Kegiatan"
      subtitle={`Periode: ${activePeriod.name} — sumber data Rencana Besok & operasional harian`}
      icon={CalendarDays} endpoint="/schedules" entityName="Jadwal"
      searchPlaceholder="Cari nama sekolah..."
      canCreate={can("SCHEDULE_CREATE")} canEdit={can("SCHEDULE_UPDATE")} canArchive={can("SCHEDULE_UPDATE")}
      defaults={{ school_id: "", date: "", start_time: "07:00", end_time: "12:00", status: "PLANNED", notes: "" }}
      transformSubmit={(form, editing) => ({ ...form, period_id: editing ? editing.period_id : activePeriod.id })}
      columns={[
        { key: "date", label: "Tanggal", render: (r) => shortDate(r.date) },
        { key: "school_name", label: "Sekolah" },
        { key: "time", label: "Waktu", render: (r) => `${r.start_time || "-"} – ${r.end_time || "-"}` },
        { key: "status", label: "Status", render: (r) => <StatusBadge value={r.status} /> },
        { key: "notes", label: "Catatan", render: (r) => r.notes || "-" },
      ]}
      formFields={[
        { name: "school_id", label: "Sekolah", type: "select", required: true, options: schoolOptions },
        { name: "date", label: "Tanggal", type: "date", required: true, colSpan: 1 },
        { name: "status", label: "Status", type: "select", colSpan: 1, options: STATUSES.map((s) => ({ value: s, label: s })) },
        { name: "start_time", label: "Waktu Mulai", type: "time", colSpan: 1 },
        { name: "end_time", label: "Waktu Selesai", type: "time", colSpan: 1 },
        { name: "notes", label: "Catatan", type: "textarea" },
      ]}
      extraRowActions={can("SCHEDULE_UPDATE") ? (row, reload) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-500 hover:text-emerald-700" data-testid={`sched-status-${row.id}`}>
              <Power size={15} />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {STATUSES.map((s) => (
              <DropdownMenuItem key={s} onClick={() => changeStatus(row, s, reload)} data-testid={`sched-set-${s}`}>
                Set {s}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      ) : null}
    />
  );
}
