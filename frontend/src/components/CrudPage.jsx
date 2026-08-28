import React, { useEffect, useState, useCallback } from "react";
import api, { apiError } from "@/lib/api";
import { toast } from "sonner";
import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import MultiSelect from "@/components/MultiSelect";
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
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Plus, Search, Pencil, Archive, Loader2 } from "lucide-react";

export default function CrudPage({
  title, subtitle, icon, endpoint, entityName,
  columns, formFields, defaults = {}, searchPlaceholder = "Cari...",
  canCreate, canEdit, canArchive, extraRowActions, transformSubmit,
}) {
  const [rows, setRows] = useState([]);
  const [status, setStatus] = useState("loading"); // loading|ok|error|empty
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(defaults);
  const [saving, setSaving] = useState(false);
  const [archiveTarget, setArchiveTarget] = useState(null);
  const limit = 20;

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const { data } = await api.get(endpoint, { params: { search, page, limit } });
      setRows(data.items || []);
      setTotal(data.total || 0);
      setStatus((data.items || []).length === 0 ? "empty" : "ok");
    } catch (e) {
      setStatus("error");
    }
  }, [endpoint, search, page]);

  useEffect(() => { load(); }, [load]);

  const openCreate = () => { setEditing(null); setForm(defaults); setDialogOpen(true); };
  const openEdit = (row) => {
    const f = {};
    formFields.forEach((fl) => {
      let v = row[fl.name] ?? defaults[fl.name] ?? (fl.type === "multiselect" ? [] : "");
      if (fl.type === "select" && typeof v === "boolean") v = String(v);
      f[fl.name] = v;
    });
    setForm(f); setEditing(row); setDialogOpen(true);
  };

  const submit = async () => {
    for (const fl of formFields) {
      if (fl.required && (form[fl.name] === "" || form[fl.name] == null)) {
        toast.error(`${fl.label} wajib diisi.`);
        return;
      }
    }
    setSaving(true);
    try {
      const body = transformSubmit ? transformSubmit(form, editing) : form;
      if (editing) await api.put(`${endpoint}/${editing.id}`, body);
      else await api.post(endpoint, body);
      toast.success(editing ? `${entityName} berhasil diperbarui.` : `${entityName} berhasil ditambahkan.`);
      setDialogOpen(false);
      load();
    } catch (e) {
      toast.error(apiError(e.response?.data?.detail) || "Gagal menyimpan data.");
    } finally {
      setSaving(false);
    }
  };

  const doArchive = async () => {
    try {
      await api.delete(`${endpoint}/${archiveTarget.id}`);
      toast.success(`${entityName} berhasil diarsipkan.`);
      setArchiveTarget(null);
      load();
    } catch (e) {
      toast.error(apiError(e.response?.data?.detail) || "Gagal mengarsipkan.");
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / limit));
  const setField = (name, val) => setForm((f) => ({ ...f, [name]: val }));

  return (
    <div className="animate-fade-up">
      <PageHeader
        title={title} subtitle={subtitle} icon={icon}
        actions={canCreate && (
          <Button onClick={openCreate} data-testid={`add-${entityName}-btn`} className="bg-emerald-900 hover:bg-emerald-800">
            <Plus size={16} className="mr-1.5" /> Tambah
          </Button>
        )}
      />

      <div className="rounded-lg border border-slate-200 bg-white">
        <div className="p-4 border-b border-slate-100">
          <div className="relative max-w-sm">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <Input
              value={search}
              onChange={(e) => { setPage(1); setSearch(e.target.value); }}
              placeholder={searchPlaceholder}
              className="pl-9 border-slate-200"
              data-testid="search-input"
            />
          </div>
        </div>

        {status === "loading" && <LoadingState />}
        {status === "error" && <ErrorState onRetry={load} />}
        {status === "empty" && (
          <EmptyState
            title="Belum ada data"
            desc={search ? "Tidak ada hasil untuk pencarian ini." : `Belum ada data ${entityName}.`}
            action={canCreate && !search && (
              <Button onClick={openCreate} className="bg-emerald-900 hover:bg-emerald-800" data-testid="empty-add-btn">
                <Plus size={16} className="mr-1.5" /> Tambah {entityName}
              </Button>
            )}
          />
        )}

        {status === "ok" && (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    {columns.map((c) => (
                      <TableHead key={c.key} className="text-[11px] uppercase tracking-wider text-slate-500">
                        {c.label}
                      </TableHead>
                    ))}
                    {(canEdit || canArchive || extraRowActions) && <TableHead className="text-right text-[11px] uppercase tracking-wider text-slate-500">Aksi</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((row) => (
                    <TableRow key={row.id} className="hover:bg-slate-50" data-testid={`row-${row.id}`}>
                      {columns.map((c) => (
                        <TableCell key={c.key} className="text-sm text-slate-700">
                          {c.render ? c.render(row) : (row[c.key] ?? "-")}
                        </TableCell>
                      ))}
                      {(canEdit || canArchive || extraRowActions) && (
                        <TableCell className="text-right whitespace-nowrap">
                          {extraRowActions && extraRowActions(row, load)}
                          {canEdit && (
                            <Button variant="ghost" size="icon" onClick={() => openEdit(row)} data-testid={`edit-${row.id}`} className="h-8 w-8 text-slate-500 hover:text-emerald-700">
                              <Pencil size={15} />
                            </Button>
                          )}
                          {canArchive && (
                            <Button variant="ghost" size="icon" onClick={() => setArchiveTarget(row)} data-testid={`archive-${row.id}`} className="h-8 w-8 text-slate-500 hover:text-red-600">
                              <Archive size={15} />
                            </Button>
                          )}
                        </TableCell>
                      )}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="flex items-center justify-between p-4 border-t border-slate-100 text-sm text-slate-500">
              <span>Total {total} data</span>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)} data-testid="prev-page">Sebelumnya</Button>
                <span className="px-2">Hal {page} / {totalPages}</span>
                <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)} data-testid="next-page">Berikutnya</Button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Create / Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading">{editing ? `Ubah ${entityName}` : `Tambah ${entityName}`}</DialogTitle>
            <DialogDescription className="sr-only">Formulir data {entityName}</DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-2">
            {formFields.map((fl) => (
              <div key={fl.name} className={fl.colSpan === 1 ? "col-span-1" : "col-span-2"}>
                <Label className="text-sm text-slate-700 mb-1.5 block">
                  {fl.label} {fl.required && <span className="text-red-500">*</span>}
                </Label>
                {fl.type === "textarea" ? (
                  <Textarea value={form[fl.name] ?? ""} onChange={(e) => setField(fl.name, e.target.value)} className="border-slate-200" data-testid={`field-${fl.name}`} />
                ) : fl.type === "select" ? (
                  <Select value={form[fl.name] ?? ""} onValueChange={(v) => setField(fl.name, v)}>
                    <SelectTrigger className="border-slate-200" data-testid={`field-${fl.name}`}><SelectValue placeholder={`Pilih ${fl.label}`} /></SelectTrigger>
                    <SelectContent>
                      {(fl.options || []).map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                ) : fl.type === "multiselect" ? (
                  <MultiSelect options={fl.options || []} value={form[fl.name] || []} onChange={(v) => setField(fl.name, v)} placeholder={`Pilih ${fl.label}`} testid={`field-${fl.name}`} />
                ) : (
                  <Input
                    type={fl.type === "number" ? "number" : fl.type === "password" ? "password" : fl.type === "date" ? "date" : fl.type === "time" ? "time" : "text"}
                    value={form[fl.name] ?? ""}
                    onChange={(e) => setField(fl.name, fl.type === "number" ? Number(e.target.value) : e.target.value)}
                    placeholder={fl.placeholder}
                    className="border-slate-200"
                    data-testid={`field-${fl.name}`}
                  />
                )}
                {fl.hint && <p className="text-xs text-slate-400 mt-1">{fl.hint}</p>}
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)} data-testid="cancel-btn">Batal</Button>
            <Button onClick={submit} disabled={saving} className="bg-emerald-900 hover:bg-emerald-800" data-testid="save-btn">
              {saving && <Loader2 size={15} className="mr-1.5 animate-spin" />} Simpan
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Archive confirm */}
      <AlertDialog open={!!archiveTarget} onOpenChange={(o) => !o && setArchiveTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Arsipkan {entityName}?</AlertDialogTitle>
            <AlertDialogDescription>
              Data akan dinonaktifkan namun tetap tersimpan untuk keperluan historis dan audit.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="archive-cancel">Batal</AlertDialogCancel>
            <AlertDialogAction onClick={doArchive} className="bg-red-600 hover:bg-red-700" data-testid="archive-confirm">
              Ya, Arsipkan
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export { StatusBadge };
