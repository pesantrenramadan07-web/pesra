import React from "react";
import { useAuth } from "@/context/AuthContext";
import { usePeriod } from "@/context/PeriodContext";
import { formatMasehi, formatHijri } from "@/lib/dates";
import { Menu, LogOut, User as UserIcon, ChevronDown, CalendarRange } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

export default function Header({ onMenu }) {
  const { user, logout } = useAuth();
  const { periods, activePeriod, setActivePeriod } = usePeriod();
  const today = new Date().toISOString();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-slate-200 bg-white/95 backdrop-blur px-4 sm:px-6">
      <Button
        variant="ghost" size="icon" className="lg:hidden" onClick={onMenu}
        data-testid="menu-toggle"
      >
        <Menu size={20} />
      </Button>

      <div className="hidden md:flex items-center gap-2 min-w-0">
        <CalendarRange size={16} className="text-emerald-700 shrink-0" />
        {periods.length > 0 ? (
          <Select
            value={activePeriod?.id || ""}
            onValueChange={(v) => setActivePeriod(periods.find((p) => p.id === v))}
          >
            <SelectTrigger className="h-9 w-[240px] border-slate-200" data-testid="period-selector">
              <SelectValue placeholder="Pilih Periode" />
            </SelectTrigger>
            <SelectContent>
              {periods.map((p) => (
                <SelectItem key={p.id} value={p.id} data-testid={`period-opt-${p.id}`}>
                  {p.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <span className="text-sm text-slate-500">Tidak ada periode</span>
        )}
        {activePeriod?.is_test && (
          <span className="rounded bg-sky-100 text-sky-700 text-[10px] font-semibold px-2 py-0.5 uppercase tracking-wide">
            Mode Testing
          </span>
        )}
      </div>

      <div className="ml-auto flex items-center gap-4">
        <div className="hidden sm:block text-right leading-tight">
          <p className="text-xs font-medium text-slate-700" data-testid="header-masehi">{formatMasehi(today)}</p>
          <p className="text-[11px] text-emerald-700" data-testid="header-hijri">{formatHijri(today)}</p>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="flex items-center gap-2 rounded-md border border-slate-200 pl-1.5 pr-2 py-1.5 hover:bg-slate-50 transition-colors duration-200"
              data-testid="user-menu-trigger"
            >
              <span className="flex h-7 w-7 items-center justify-center rounded-md bg-emerald-900 text-white text-xs font-semibold">
                {(user?.name || "?").slice(0, 1).toUpperCase()}
              </span>
              <span className="hidden sm:block text-left leading-tight">
                <span className="block text-xs font-semibold text-slate-800 max-w-[120px] truncate">{user?.name}</span>
                <span className="block text-[10px] text-slate-500">{user?.role_label}</span>
              </span>
              <ChevronDown size={14} className="text-slate-400" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52">
            <DropdownMenuLabel className="flex items-center gap-2">
              <UserIcon size={14} /> {user?.email}
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout} data-testid="logout-btn" className="text-red-600 focus:text-red-600">
              <LogOut size={14} className="mr-2" /> Keluar
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
