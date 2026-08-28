import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, Info, Circle } from "lucide-react";

const MAP = {
  ACTIVE: { label: "Aktif", cls: "bg-emerald-50 text-emerald-700 border-emerald-200", Icon: CheckCircle2 },
  INACTIVE: { label: "Nonaktif", cls: "bg-slate-100 text-slate-600 border-slate-200", Icon: Circle },
  DRAFT: { label: "Draft", cls: "bg-slate-100 text-slate-600 border-slate-200", Icon: Circle },
  TESTING: { label: "Testing", cls: "bg-sky-50 text-sky-700 border-sky-200", Icon: Info },
  HISTORICAL: { label: "Historis", cls: "bg-amber-50 text-amber-700 border-amber-200", Icon: Info },
  COMPLETED: { label: "Selesai", cls: "bg-emerald-50 text-emerald-700 border-emerald-200", Icon: CheckCircle2 },
  ARCHIVED: { label: "Diarsipkan", cls: "bg-slate-100 text-slate-500 border-slate-200", Icon: Circle },
  SUCCESS: { label: "Sukses", cls: "bg-emerald-50 text-emerald-700 border-emerald-200", Icon: CheckCircle2 },
  WARNING: { label: "Perhatian", cls: "bg-amber-50 text-amber-700 border-amber-200", Icon: AlertTriangle },
  DANGER: { label: "Bahaya", cls: "bg-red-50 text-red-700 border-red-200", Icon: XCircle },
  UPLOADED: { label: "Diunggah", cls: "bg-slate-100 text-slate-600 border-slate-200", Icon: Circle },
  VALIDATED: { label: "Tervalidasi", cls: "bg-sky-50 text-sky-700 border-sky-200", Icon: Info },
  IMPORTED: { label: "Terimpor", cls: "bg-emerald-50 text-emerald-700 border-emerald-200", Icon: CheckCircle2 },
  CANCELLED: { label: "Dibatalkan", cls: "bg-slate-100 text-slate-500 border-slate-200", Icon: XCircle },
  VALID: { label: "Valid", cls: "bg-emerald-50 text-emerald-700 border-emerald-200", Icon: CheckCircle2 },
  INVALID: { label: "Tidak Valid", cls: "bg-red-50 text-red-700 border-red-200", Icon: XCircle },
  DUPLICATE: { label: "Duplikat", cls: "bg-amber-50 text-amber-700 border-amber-200", Icon: AlertTriangle },
};

export default function StatusBadge({ value, label, tone }) {
  const key = tone || value;
  const cfg = MAP[key] || { label: label || value, cls: "bg-slate-100 text-slate-600 border-slate-200", Icon: Circle };
  const Icon = cfg.Icon;
  return (
    <span
      data-testid={`status-badge-${(value || "").toLowerCase()}`}
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium ${cfg.cls}`}
    >
      <Icon size={13} />
      {label || cfg.label}
    </span>
  );
}
