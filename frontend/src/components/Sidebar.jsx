import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import { NAV } from "@/config/nav";
import { useAuth } from "@/context/AuthContext";
import { Moon } from "lucide-react";

export default function Sidebar({ onNavigate }) {
  const { can } = useAuth();

  return (
    <div className="flex h-full flex-col bg-emerald-950 text-emerald-50">
      <div className="flex items-center gap-3 px-5 h-16 border-b border-emerald-900/60 shrink-0">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-amber-500 text-emerald-950">
          <Moon size={20} fill="currentColor" />
        </div>
        <div className="leading-tight">
          <p className="font-heading font-extrabold tracking-tight text-white">SIMPESRA</p>
          <p className="text-[10px] uppercase tracking-[0.18em] text-emerald-300">LIM · Monitoring</p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        {NAV.map((section, si) => {
          const visible = section.items.filter((it) => can(it.perm));
          if (visible.length === 0) return null;
          return (
            <div key={si}>
              {section.label && (
                <p className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-400/80">
                  {section.label}
                </p>
              )}
              <div className="space-y-0.5">
                {visible.map((it) => {
                  const Icon = it.icon;
                  return (
                    <NavLink
                      key={it.path}
                      to={it.path}
                      end={it.path === "/"}
                      onClick={onNavigate}
                      data-testid={`nav-${it.path === "/" ? "dashboard" : it.path.slice(1)}`}
                      className={({ isActive }) =>
                        `group flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors duration-200 ${
                          isActive
                            ? "bg-emerald-800/80 text-white font-medium"
                            : "text-emerald-100/80 hover:bg-emerald-900/60 hover:text-white"
                        }`
                      }
                    >
                      <Icon size={17} className="shrink-0" />
                      <span className="truncate">{it.label}</span>
                      {it.soon && (
                        <span className="ml-auto text-[9px] uppercase bg-emerald-800 text-emerald-200 px-1.5 py-0.5 rounded">
                          Segera
                        </span>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          );
        })}
      </nav>
    </div>
  );
}
