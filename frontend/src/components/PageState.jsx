import React from "react";
import { Loader2, Inbox, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export function LoadingState({ label = "Memuat data..." }) {
  return (
    <div data-testid="loading-state" className="flex flex-col items-center justify-center py-16 text-slate-500">
      <Loader2 className="animate-spin mb-3" size={28} />
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function EmptyState({ title = "Belum ada data", desc, action }) {
  return (
    <div data-testid="empty-state" className="flex flex-col items-center justify-center py-16 text-center">
      <div className="rounded-full bg-slate-100 p-4 mb-4">
        <Inbox className="text-slate-400" size={28} />
      </div>
      <p className="font-heading font-semibold text-slate-700">{title}</p>
      {desc && <p className="text-sm text-slate-500 mt-1 max-w-sm">{desc}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorState({ onRetry, message = "Data belum dapat dimuat." }) {
  return (
    <div data-testid="error-state" className="flex flex-col items-center justify-center py-16 text-center">
      <div className="rounded-full bg-red-50 p-4 mb-4">
        <AlertCircle className="text-red-500" size={28} />
      </div>
      <p className="font-heading font-semibold text-slate-700">{message}</p>
      {onRetry && (
        <Button variant="outline" className="mt-4" onClick={onRetry} data-testid="retry-btn">
          Coba lagi
        </Button>
      )}
    </div>
  );
}
