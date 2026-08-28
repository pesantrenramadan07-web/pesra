import React, { useEffect, useState, useCallback } from "react";
import api, { apiError } from "@/lib/api";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { usePeriod } from "@/context/PeriodContext";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import { LoadingState, EmptyState, ErrorState } from "@/components/PageState";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  ClipboardList, Upload, Download, ArrowLeft, FileSpreadsheet, Loader2,
  CheckCircle2, XCircle, AlertTriangle, Eye, Ban, Import,
} from "lucide-react";
import { dateTime } from "@/lib/dates";

const STAT_FILTERS = [
  { key: "", label: "Semua" },
  { key: "VALID", label: "Valid" },
  { key: "INVALID", label: "Tidak Valid" },
  { key: "DUPLICATE", label: "Duplikat" },
];

export default function Roster() {
  const { can } = useAuth();
  const { activePeriod } = usePeriod();
  const [view, setView] = useState("list"); // list | detail
  const [current, setCurrent] = useState(null);

  return view === "list" ? (
    <RosterList
      canUpload={can("ROSTER_UPLOAD")}
      onOpen={(r) => { setCurrent(r); setView("detail"); }}
      activePeriod={activePeriod}
    />
  ) : (
    <RosterDetail
      roster={current}
      canImport={can("ROSTER_IMPORT")}
      canUpload={can("ROSTER_UPLOAD")}
      onBack={() => { setCurrent(null); setView("list"); }}
    />
  );
}

/* ---------------- LIST ---------------- */
function RosterList({ canUpload, onOpen, activePeriod }) {
  const [rows, setRows] = useState([]);
  const [status, setStatus] = useState("loading");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [file, setFile] = useState(null);
  const [notes, setNotes] = useState("");
  const [uploading, setUploading] = useState(false);

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const { data } = await api.get("/rosters", { params: { period_id: activePeriod?.id, limit: 100 } });
      setRows(data.items || []);
      setStatus((data.items || []).length === 0 ? "empty" : "ok");
    } catch { setStatus("error"); }
  }, [activePeriod]);
  useEffect(() => { load(); }, [load]);

  const downloadTemplate = async () => {
    try {
      const res = await api.get("/rosters/template", { responseType: "blob" });
      const url = window.URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url; a.download = "template_roster.xlsx"; a.click();
      window.URL.revokeObjectURL(url);
    } catch { toast.error("Gagal mengunduh template."); }
  };

  const doUpload = async () => {
    if (!activePeriod?.id) { toast.error("Pilih periode terlebih dahulu."); return; }
    if (!file) { toast.error("Pilih file Excel terlebih dahulu."); return; }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const { data } = await api.post("/rosters/upload", fd, {
        params: { period_id: activePeriod.id, notes },
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success(`Roster v${data.version} berhasil diunggah & divalidasi.`);
      setUploadOpen(false); setFile(null); setNotes("");
      onOpen(data);
    } catch (e) {
      toast.error(apiError(e.response?.data?.detail) || "Gagal mengunggah roster.");
    } finally { setUploading(false); }
  };

  return (
    <div className="animate-fade-up">
      <PageHeader
        title="Roster Induk" icon={ClipboardList}
        subtitle={activePeriod ? `Periode: ${activePeriod.name}` : "Sumber data utama penugasan"}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={downloadTemplate} data-testid="download-template-btn">
              <Download size={16} className="mr-1.5" /> Template
            </Button>
            {canUpload && (
              <Button onClick={() => setUploadOpen(true)} className="bg-emerald-900 hover:bg-emerald-800" data-testid="upload-roster-btn">
                <Upload size={16} className="mr-1.5" /> Unggah Roster
              </Button>
            )}
          </div>
        }
      />

      <div className="rounded-lg border border-slate-200 bg-white">
        {status === "loading" && <LoadingState />}
        {status === "error" && <ErrorState onRetry={load} />}
        {status === "empty" && (
          <EmptyState title="Belum ada roster"
            desc="Unggah file Excel roster untuk periode ini. Unduh template untuk format yang benar."
            action={canUpload && (
              <Button onClick={() => setUploadOpen(true)} className="bg-emerald-900 hover:bg-emerald-800" data-testid="empty-upload-btn">
                <Upload size={16} className="mr-1.5" /> Unggah Roster
              </Button>
            )} />
        )}
        {status === "ok" && (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  {["Versi", "Nama File", "Status", "Valid", "Tidak Valid", "Duplikat", "Diunggah", "Aksi"].map((h) => (
                    <TableHead key={h} className="text-[11px] uppercase tracking-wider text-slate-500">{h}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((r) => (
                  <TableRow key={r.id} className="hover:bg-slate-50" data-testid={`roster-row-${r.id}`}>
                    <TableCell className="font-semibold text-slate-800">v{r.version}</TableCell>
                    <TableCell className="text-sm text-slate-700 flex items-center gap-2">
                      <FileSpreadsheet size={15} className="text-emerald-600" /> {r.original_filename}
                    </TableCell>
                    <TableCell><StatusBadge value={r.status} /></TableCell>
                    <TableCell className="text-emerald-700 font-medium">{r.stats?.valid ?? 0}</TableCell>
                    <TableCell className="text-red-600 font-medium">{r.stats?.invalid ?? 0}</TableCell>
                    <TableCell className="text-amber-600 font-medium">{r.stats?.duplicate ?? 0}</TableCell>
                    <TableCell className="text-xs text-slate-500">
                      {r.uploaded_by_name}<br />{dateTime(r.uploaded_at)}
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" onClick={() => onOpen(r)} data-testid={`view-roster-${r.id}`} className="text-emerald-700">
                        <Eye size={15} className="mr-1" /> Lihat
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="font-heading">Unggah Roster Induk</DialogTitle>
            <DialogDescription>
              File Excel (.xlsx) untuk periode <strong>{activePeriod?.name || "-"}</strong>. Kolom wajib: Sekolah, Pengajar.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label className="text-sm mb-1.5 block">File Excel</Label>
              <Input type="file" accept=".xlsx,.xls" onChange={(e) => setFile(e.target.files?.[0] || null)} data-testid="roster-file-input" className="border-slate-200" />
            </div>
            <div>
              <Label className="text-sm mb-1.5 block">Catatan (opsional)</Label>
              <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} className="border-slate-200" data-testid="roster-notes" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setUploadOpen(false)}>Batal</Button>
            <Button onClick={doUpload} disabled={uploading} className="bg-emerald-900 hover:bg-emerald-800" data-testid="submit-upload-btn">
              {uploading && <Loader2 size={15} className="mr-1.5 animate-spin" />} Unggah & Validasi
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

/* ---------------- DETAIL / PREVIEW ---------------- */
function RosterDetail({ roster: initial, canImport, canUpload, onBack }) {
  const [roster, setRoster] = useState(initial);
  const [rows, setRows] = useState([]);
  const [filter, setFilter] = useState("");
  const [status, setStatus] = useState("loading");
  const [importing, setImporting] = useState(false);
  const [confirmImport, setConfirmImport] = useState(false);
  const [confirmCancel, setConfirmCancel] = useState(false);

  const refreshRoster = useCallback(async () => {
    try {
      const { data } = await api.get(`/rosters/${roster.id}`);
      setRoster(data);
    } catch {}
  }, [roster.id]);

  const loadRows = useCallback(async () => {
    setStatus("loading");
    try {
      const src = roster.status === "IMPORTED" ? `/rosters/${roster.id}/details` : `/rosters/${roster.id}/rows`;
      const { data } = await api.get(src, { params: { status: filter, limit: 200 } });
      setRows(data.items || []);
      setStatus("ok");
    } catch { setStatus("error"); }
  }, [roster.id, roster.status, filter]);

  useEffect(() => { loadRows(); }, [loadRows]);

  const s = roster.stats || {};
  const canDoImport = canImport && roster.status === "VALIDATED" && (s.invalid ?? 0) === 0;

  const doImport = async () => {
    setImporting(true);
    try {
      const { data } = await api.post(`/rosters/${roster.id}/import`);
      toast.success(data.message || "Import berhasil.");
      setConfirmImport(false);
      await refreshRoster(); loadRows();
    } catch (e) {
      toast.error(apiError(e.response?.data?.detail) || "Gagal import roster.");
    } finally { setImporting(false); }
  };

  const doCancel = async () => {
    try {
      await api.post(`/rosters/${roster.id}/cancel`);
      toast.success("Roster dibatalkan.");
      setConfirmCancel(false);
      await refreshRoster();
    } catch (e) { toast.error(apiError(e.response?.data?.detail)); }
  };

  const isImported = roster.status === "IMPORTED";

  return (
    <div className="animate-fade-up">
      <button onClick={onBack} className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-emerald-700 mb-4" data-testid="roster-back-btn">
        <ArrowLeft size={15} /> Kembali ke daftar
      </button>

      <PageHeader
        title={`Roster v${roster.version}`} icon={FileSpreadsheet}
        subtitle={roster.original_filename}
        actions={
          <div className="flex items-center gap-2">
            <StatusBadge value={roster.status} />
            {canUpload && roster.status === "VALIDATED" && (
              <Button variant="outline" onClick={() => setConfirmCancel(true)} data-testid="cancel-roster-btn" className="text-red-600 border-red-200 hover:bg-red-50">
                <Ban size={15} className="mr-1.5" /> Batalkan
              </Button>
            )}
            {canDoImport && (
              <Button onClick={() => setConfirmImport(true)} className="bg-emerald-900 hover:bg-emerald-800" data-testid="confirm-import-btn">
                <Import size={15} className="mr-1.5" /> Konfirmasi Import
              </Button>
            )}
          </div>
        }
      />

      {/* stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { k: "total", label: "Total Baris", cls: "text-slate-800", Icon: ClipboardList },
          { k: "valid", label: "Valid", cls: "text-emerald-700", Icon: CheckCircle2 },
          { k: "invalid", label: "Tidak Valid", cls: "text-red-600", Icon: XCircle },
          { k: "duplicate", label: "Duplikat", cls: "text-amber-600", Icon: AlertTriangle },
        ].map(({ k, label, cls, Icon }) => (
          <div key={k} className="rounded-lg border border-slate-200 bg-white p-4" data-testid={`stat-${k}`}>
            <div className="flex items-center justify-between">
              <p className={`font-heading text-2xl font-bold ${cls}`}>{isImported && k === "valid" ? (roster.imported_count ?? s[k]) : (s[k] ?? 0)}</p>
              <Icon size={18} className={cls} />
            </div>
            <p className="text-xs text-slate-500 mt-1">{isImported && k === "valid" ? "Terimpor" : label}</p>
          </div>
        ))}
      </div>

      {roster.status === "VALIDATED" && (s.invalid ?? 0) > 0 && (
        <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-4 py-2.5 text-red-700 text-sm mb-4" data-testid="import-blocked-warning">
          <AlertTriangle size={16} /> Terdapat <strong>{s.invalid}</strong> baris tidak valid. Import ditolak hingga file diperbaiki dan diunggah ulang.
        </div>
      )}
      {isImported && (
        <div className="flex items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-emerald-700 text-sm mb-4" data-testid="imported-banner">
          <CheckCircle2 size={16} /> Roster telah diimpor ({roster.imported_count} baris) pada {dateTime(roster.imported_at)}.
        </div>
      )}

      {/* filter tabs (preview only) */}
      {!isImported && (
        <div className="flex gap-2 mb-3">
          {STAT_FILTERS.map((f) => (
            <button key={f.key} onClick={() => setFilter(f.key)} data-testid={`filter-${f.key || "all"}`}
              className={`rounded-md px-3 py-1.5 text-sm border transition-colors ${filter === f.key ? "bg-emerald-900 text-white border-emerald-900" : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"}`}>
              {f.label}
            </button>
          ))}
        </div>
      )}

      <div className="rounded-lg border border-slate-200 bg-white overflow-x-auto">
        {status === "loading" && <LoadingState />}
        {status === "error" && <ErrorState onRetry={loadRows} />}
        {status === "ok" && rows.length === 0 && <EmptyState title="Tidak ada baris" desc="Tidak ada data untuk filter ini." />}
        {status === "ok" && rows.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                {isImported
                  ? ["Pengajar", "Posisi", "Koordinator", "Armada"].map((h) => <TableHead key={h} className="text-[11px] uppercase tracking-wider text-slate-500">{h}</TableHead>)
                  : ["Baris", "Sekolah", "Pengajar", "Status", "Keterangan"].map((h) => <TableHead key={h} className="text-[11px] uppercase tracking-wider text-slate-500">{h}</TableHead>)}
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((r) => isImported ? (
                <TableRow key={r.id} className="hover:bg-slate-50">
                  <TableCell className="text-sm text-slate-700">{r.teacher_name}</TableCell>
                  <TableCell className="text-sm text-slate-600">{r.position || "-"}</TableCell>
                  <TableCell className="text-sm text-slate-600">{r.coordinator || "-"}</TableCell>
                  <TableCell className="text-sm text-slate-600">{r.vehicle_hint || "-"}</TableCell>
                </TableRow>
              ) : (
                <TableRow key={r.id} className="hover:bg-slate-50" data-testid={`preview-row-${r.row_number}`}>
                  <TableCell className="text-slate-400 text-sm">{r.row_number}</TableCell>
                  <TableCell className="text-sm text-slate-700">{r.raw_data?.Sekolah}</TableCell>
                  <TableCell className="text-sm text-slate-700">{r.raw_data?.Pengajar || <span className="text-slate-300">(kosong)</span>}</TableCell>
                  <TableCell><StatusBadge value={r.validation_status} /></TableCell>
                  <TableCell className="text-xs text-slate-500">{r.validation_message || "-"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      <AlertDialog open={confirmImport} onOpenChange={setConfirmImport}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Konfirmasi Import Roster?</AlertDialogTitle>
            <AlertDialogDescription>
              {s.valid} baris valid akan diimpor ke sistem sebagai data periode ini. Pengajar baru akan otomatis dibuat di Master Pengajar. Tindakan ini tercatat pada audit trail.
              {(s.duplicate ?? 0) > 0 && <span className="block mt-2 text-amber-700">{s.duplicate} baris duplikat akan dilewati.</span>}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="import-cancel">Batal</AlertDialogCancel>
            <AlertDialogAction onClick={doImport} disabled={importing} className="bg-emerald-900 hover:bg-emerald-800" data-testid="import-confirm">
              {importing && <Loader2 size={15} className="mr-1.5 animate-spin" />} Ya, Import
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={confirmCancel} onOpenChange={setConfirmCancel}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Batalkan Roster?</AlertDialogTitle>
            <AlertDialogDescription>
              Roster v{roster.version} akan ditandai DIBATALKAN dan tidak dapat diimpor. Riwayat tetap tersimpan.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Batal</AlertDialogCancel>
            <AlertDialogAction onClick={doCancel} className="bg-red-600 hover:bg-red-700" data-testid="cancel-confirm">Ya, Batalkan</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
