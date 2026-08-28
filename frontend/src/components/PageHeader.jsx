import React from "react";

export default function PageHeader({ title, subtitle, icon: Icon, actions }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div className="flex items-start gap-3">
        {Icon && (
          <div className="flex h-11 w-11 items-center justify-center rounded-md bg-emerald-900 text-white shrink-0">
            <Icon size={22} />
          </div>
        )}
        <div>
          <h1 className="font-heading text-2xl sm:text-3xl font-bold tracking-tight text-emerald-950">{title}</h1>
          {subtitle && <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
