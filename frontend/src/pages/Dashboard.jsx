import React, { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { usePeriod } from "@/context/PeriodContext";
import { formatMasehi, formatHijri } from "@/lib/dates";
import { LoadingState, ErrorState } from "@/components/PageState";
import StatusBadge from "@/components/StatusBadge";
import {
  School, GraduationCap, Bus, Users2, UserCog, CalendarClock, Sunrise,
  AlertTriangle, Activity, CheckCircle2, Moon, Info,
} from "lucide-react";
import { dateTime } from "@/lib/dates";

const ICONS = { schools: School, teachers: GraduationCap, vehicles: Bus, daily_board: Users2, officers: UserCog };
const COLORS = {
  schools: "bg-emerald-50 text-emerald-700",
  teachers: "bg-sky-50 text-sky-700",
  vehicles: "bg-amber-50 text-amber-700",
  daily_board: "bg-violet-50 text-violet-700",
  officers: "bg-rose-50 text-rose-700",
};

export default function Dashboard() {
  const { user } = useAuth();
  const { activePeriod } = usePeriod();
  const [data, setData] = useState(null);
  const [status, setStatus] = useState("loading");
  const today = new Date().toISOString();

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const { data } = await api.get("/dashboard/summary", {
        params: { period_id: activePeriod?.id || undefined },
      });
      setData(data);
      setStatus("ok");
    } catch {
      setStatus("error");
    }
  }, [activePeriod]);

  useEffect(() => { load(); }, [load]);

  if (status === "loading") return <LoadingState label="Memuat dashboard..." />;
  if (status === "error") return <ErrorState onRetry={load} />;

  const cards = Object.entries(data.cards || {});

  return (
    <div className="animate-fade-up space-y-6">
      {/* Greeting + period */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="font-heading text-2xl sm:text-3xl font-bold tracking-tight text-emerald-950">
            Assalamu'alaikum, {user?.name?.split(" ")[0]}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            {formatMasehi(today)} &middot; <span className="text-emerald-700">{formatHijri(today)}</span>
          </p>
        </div>
        {data.period ? (
          <div className="flex items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2">
            <CalendarClock size={16} className="text-emerald-700" />
            <div className="leading-tight">
              <p className="text-xs font-semibold text-emerald-900" data-testid="dash-period-name">{data.period.name}</p>
              <p className="text-[11px] text-emerald-600">{data.period.status}{data.is_test_mode ? " · TESTING" : ""}</p>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-amber-700 text-sm">
            <Info size={16} /> Belum ada periode aktif
          </div>
        )}
      </div>

      {data.is_test_mode && (
        <div className="flex items-center gap-2 rounded-md border border-sky-200 bg-sky-50 px-4 py-2.5 text-sky-800 text-sm" data-testid="test-mode-banner">
          <Info size={16} /> <strong>Mode Testing.</strong> Data periode ini tidak memengaruhi laporan resmi.
        </div>
      )}

      {data.is_ahad && (
        <div className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-4 py-3 text-slate-600" data-testid="ahad-banner">
          <Moon size={18} className="text-emerald-700" /> <strong className="text-slate-800">Ahad</strong> — tidak ada kegiatan terjadwal.
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {cards.map(([key, c], i) => {
          const Icon = ICONS[key] || Activity;
          return (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="rounded-lg border border-slate-200 bg-white p-5 hover:-translate-y-[1px] transition-transform duration-200"
              data-testid={`card-${key}`}
            >
              <div className={`inline-flex h-9 w-9 items-center justify-center rounded-md ${COLORS[key] || "bg-slate-100 text-slate-600"}`}>
                <Icon size={18} />
              </div>
              <p className="mt-3 font-heading text-3xl font-bold text-slate-900">{c.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{c.label}</p>
            </motion.div>
          );
        })}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Rencana Besok */}
        <section className="rounded-lg border border-slate-200 bg-white p-6">
          <div className="flex items-center gap-2 mb-4">
            <Sunrise size={18} className="text-amber-600" />
            <h2 className="font-heading text-lg font-semibold text-emerald-950">Rencana Besok</h2>
          </div>
          {data.rencana_besok?.available ? (
            <div data-testid="rencana-besok-list">
              <div className="flex items-center gap-4 mb-3">
                <div className="rounded-md bg-amber-50 border border-amber-100 px-3 py-2 text-center">
                  <p className="font-heading text-2xl font-bold text-amber-700">{data.rencana_besok.schools}</p>
                  <p className="text-[11px] text-slate-500">Sekolah</p>
                </div>
                <p className="text-xs text-slate-500">Rencana untuk {new Date(data.rencana_besok.date).toLocaleDateString("id-ID", { weekday: "long", day: "numeric", month: "long" })}</p>
              </div>
              <ul className="divide-y divide-slate-100 border border-slate-100 rounded-md">
                {data.rencana_besok.items.map((it, i) => (
                  <li key={i} className="flex items-center justify-between px-3 py-2.5 text-sm" data-testid={`rencana-item-${i}`}>
                    <span className="text-slate-700 font-medium">{it.school_name}</span>
                    <span className="flex items-center gap-3">
                      <span className="text-xs text-slate-500">{it.start_time}–{it.end_time}</span>
                      <StatusBadge value={it.status} />
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="rounded-md bg-slate-50 border border-slate-100 p-4 text-sm text-slate-500" data-testid="rencana-besok-empty">
              Belum ada jadwal untuk besok. Tambahkan data pada modul <strong>Jadwal</strong> untuk mengisi Rencana Besok.
            </div>
          )}
        </section>

        {/* Realisasi Hari Ini */}
        <section className="rounded-lg border border-slate-200 bg-white p-6">
          <div className="flex items-center gap-2 mb-4">
            <Activity size={18} className="text-emerald-600" />
            <h2 className="font-heading text-lg font-semibold text-emerald-950">Realisasi Hari Ini</h2>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {[
              ["Sekolah", data.realisasi.schools_started, data.realisasi.schools_total],
              ["Pengajar", data.realisasi.teachers_departed, data.realisasi.teachers_total],
              ["Armada", data.realisasi.vehicles_departed, data.realisasi.vehicles_total],
            ].map(([label, a, b]) => (
              <div key={label} className="rounded-md bg-slate-50 border border-slate-100 p-3 text-center">
                <p className="font-heading text-xl font-bold text-slate-800">{a}<span className="text-slate-400 text-sm"> / {b}</span></p>
                <p className="text-xs text-slate-500 mt-0.5">{label}</p>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-400 mt-3">Angka realisasi sekolah dihitung otomatis dari status Jadwal hari ini (ONGOING/COMPLETED). Pengajar & armada menyusul pada modul operasional berikutnya.</p>
        </section>
      </div>

      {/* Perlu Perhatian */}
      <section className="rounded-lg border border-slate-200 bg-white p-6">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle size={18} className="text-amber-600" />
          <h2 className="font-heading text-lg font-semibold text-emerald-950">Perlu Perhatian</h2>
        </div>
        {(!data.perlu_perhatian || data.perlu_perhatian.length === 0) ? (
          <div className="flex items-center gap-2 text-sm text-emerald-700" data-testid="attention-empty">
            <CheckCircle2 size={16} /> Tidak ada hal yang memerlukan perhatian saat ini.
          </div>
        ) : (
          <ul className="space-y-2">
            {data.perlu_perhatian.map((p, i) => (
              <li key={i} className="flex items-center gap-2 text-sm text-amber-800">
                <AlertTriangle size={14} /> {p.message}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Recent activity */}
      {data.recent_activity && data.recent_activity.length > 0 && (
        <section className="rounded-lg border border-slate-200 bg-white p-6">
          <h2 className="font-heading text-lg font-semibold text-emerald-950 mb-4">Aktivitas Terbaru</h2>
          <ul className="divide-y divide-slate-100">
            {data.recent_activity.map((a) => (
              <li key={a.id} className="flex items-center justify-between py-2.5 text-sm">
                <span className="text-slate-700">
                  <strong>{a.user_name || "Sistem"}</strong> · {a.action} {a.entity_type} ({a.module})
                </span>
                <span className="text-xs text-slate-400">{dateTime(a.timestamp)}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
