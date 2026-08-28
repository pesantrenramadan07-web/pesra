import React, { useEffect, useState } from "react";
import api from "@/lib/api";
import PageHeader from "@/components/PageHeader";
import { LoadingState, ErrorState } from "@/components/PageState";
import { ShieldCheck, Check } from "lucide-react";

export default function Roles() {
  const [roles, setRoles] = useState([]);
  const [perms, setPerms] = useState({ modules: {}, role_permissions: {} });
  const [status, setStatus] = useState("loading");

  const load = async () => {
    setStatus("loading");
    try {
      const [r, p] = await Promise.all([api.get("/roles"), api.get("/permissions")]);
      setRoles(r.data || []);
      setPerms(p.data || { modules: {}, role_permissions: {} });
      setStatus("ok");
    } catch { setStatus("error"); }
  };
  useEffect(() => { load(); }, []);

  if (status === "loading") return <LoadingState />;
  if (status === "error") return <ErrorState onRetry={load} />;

  const allPerms = [];
  Object.entries(perms.modules).forEach(([mod, actions]) =>
    actions.forEach((a) => allPerms.push(`${mod}_${a}`)));

  return (
    <div className="animate-fade-up">
      <PageHeader title="Role & Permission" subtitle="Matriks hak akses per role (read-only pada V1)." icon={ShieldCheck} />

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {roles.map((r) => (
          <div key={r.code} className="rounded-lg border border-slate-200 bg-white p-5" data-testid={`role-card-${r.code}`}>
            <h3 className="font-heading font-semibold text-emerald-950">{r.label}</h3>
            <p className="text-xs text-slate-400 mb-2">{r.code}</p>
            <p className="text-sm text-slate-600">{r.permissions.length} permission</p>
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-slate-200 bg-white overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100">
              <th className="text-left px-4 py-3 text-[11px] uppercase tracking-wider text-slate-500 sticky left-0 bg-white">Permission</th>
              {roles.map((r) => (
                <th key={r.code} className="px-3 py-3 text-[11px] uppercase tracking-wider text-slate-500 text-center whitespace-nowrap">{r.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {allPerms.map((perm) => (
              <tr key={perm} className="border-b border-slate-50 hover:bg-slate-50">
                <td className="px-4 py-2 font-mono text-xs text-slate-700 sticky left-0 bg-white">{perm}</td>
                {roles.map((r) => (
                  <td key={r.code} className="px-3 py-2 text-center">
                    {(perms.role_permissions[r.code] || []).includes(perm)
                      ? <Check size={15} className="text-emerald-600 inline" />
                      : <span className="text-slate-200">—</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
