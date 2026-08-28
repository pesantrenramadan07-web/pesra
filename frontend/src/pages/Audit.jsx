import React, { useEffect, useState, useCallback } from "react";
import api from "@/lib/api";
import PageHeader from "@/components/PageHeader";
import { LoadingState, EmptyState, ErrorState } from "@/components/PageState";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollText, Search } from "lucide-react";
import { dateTime } from "@/lib/dates";

const ACTION_COLORS = {
  CREATE: "bg-emerald-50 text-emerald-700", UPDATE: "bg-sky-50 text-sky-700",
  ARCHIVE: "bg-amber-50 text-amber-700", DELETE: "bg-red-50 text-red-700",
  LOGIN: "bg-violet-50 text-violet-700", LOGOUT: "bg-slate-100 text-slate-600",
  UPLOAD: "bg-teal-50 text-teal-700", EXPORT: "bg-indigo-50 text-indigo-700",
};

export default function Audit() {
  const [rows, setRows] = useState([]);
  const [status, setStatus] = useState("loading");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 25;

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const { data } = await api.get("/audit_logs", { params: { search, page, limit } });
      setRows(data.items || []);
      setTotal(data.total || 0);
      setStatus((data.items || []).length === 0 ? "empty" : "ok");
    } catch { setStatus("error"); }
  }, [search, page]);
  useEffect(() => { load(); }, [load]);

  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="animate-fade-up">
      <PageHeader title="Audit Trail" subtitle="Rekam jejak perubahan data penting." icon={ScrollText} />
      <div className="rounded-lg border border-slate-200 bg-white">
        <div className="p-4 border-b border-slate-100">
          <div className="relative max-w-sm">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <Input value={search} onChange={(e) => { setPage(1); setSearch(e.target.value); }}
              placeholder="Cari user / entity..." className="pl-9 border-slate-200" data-testid="audit-search" />
          </div>
        </div>
        {status === "loading" && <LoadingState />}
        {status === "error" && <ErrorState onRetry={load} />}
        {status === "empty" && <EmptyState title="Belum ada log" desc="Aktivitas akan tercatat di sini." />}
        {status === "ok" && (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    {["Waktu", "User", "Aksi", "Modul", "Entity"].map((h) => (
                      <th key={h} className="text-left px-4 py-3 text-[11px] uppercase tracking-wider text-slate-500">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.id} className="border-b border-slate-50 hover:bg-slate-50" data-testid={`audit-row-${r.id}`}>
                      <td className="px-4 py-2.5 text-slate-500 whitespace-nowrap">{dateTime(r.timestamp)}</td>
                      <td className="px-4 py-2.5 text-slate-700">{r.user_name || "-"}</td>
                      <td className="px-4 py-2.5">
                        <span className={`rounded px-2 py-0.5 text-xs font-medium ${ACTION_COLORS[r.action] || "bg-slate-100 text-slate-600"}`}>{r.action}</span>
                      </td>
                      <td className="px-4 py-2.5 text-slate-600">{r.module}</td>
                      <td className="px-4 py-2.5 text-slate-600">{r.entity_type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex items-center justify-between p-4 border-t border-slate-100 text-sm text-slate-500">
              <span>Total {total} log</span>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Sebelumnya</Button>
                <span className="px-2">Hal {page} / {totalPages}</span>
                <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Berikutnya</Button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
