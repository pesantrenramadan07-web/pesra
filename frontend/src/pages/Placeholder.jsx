import React from "react";
import PageHeader from "@/components/PageHeader";
import { Construction } from "lucide-react";

export default function Placeholder({ title, icon }) {
  return (
    <div className="animate-fade-up">
      <PageHeader title={title} icon={icon} />
      <div className="rounded-lg border border-dashed border-slate-300 bg-white p-12 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-amber-50">
          <Construction className="text-amber-600" size={26} />
        </div>
        <h2 className="font-heading text-lg font-semibold text-slate-800">Modul Segera Hadir</h2>
        <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
          Modul <strong>{title}</strong> merupakan bagian dari alur operasional harian dan akan tersedia pada iterasi berikutnya. Fondasi (Autentikasi, Role &amp; Scope, Master Data, Periode, Dashboard) telah selesai.
        </p>
      </div>
    </div>
  );
}
