import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import api, { apiError } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Moon, Loader2, ArrowLeft } from "lucide-react";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const nav = useNavigate();
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    if (password.length < 6) { setError("Password minimal 6 karakter."); return; }
    setLoading(true); setError("");
    try {
      await api.post("/auth/reset-password", { token, password });
      toast.success("Password berhasil diperbarui. Silakan masuk.");
      nav("/login");
    } catch (err) {
      setError(apiError(err.response?.data?.detail));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-emerald-900 text-white">
            <Moon size={22} fill="currentColor" />
          </div>
          <span className="font-heading font-extrabold text-xl tracking-tight text-emerald-950">SIMPESRA LIM</span>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-6">
          <h2 className="font-heading text-xl font-bold text-emerald-950">Reset Password</h2>
          <p className="text-sm text-slate-500 mt-1 mb-5">Masukkan password baru Anda.</p>
          {!token && <p className="text-sm text-red-600 mb-3">Token tidak ditemukan pada tautan.</p>}
          {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
          <form onSubmit={submit} className="space-y-4">
            <div>
              <Label className="text-sm text-slate-700 mb-1.5 block">Password Baru</Label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
                className="border-slate-200" data-testid="reset-password" />
            </div>
            <Button type="submit" disabled={loading || !token} className="w-full bg-emerald-900 hover:bg-emerald-800" data-testid="reset-submit">
              {loading && <Loader2 size={16} className="mr-2 animate-spin" />} Simpan Password
            </Button>
          </form>
        </div>
        <div className="mt-4 text-center">
          <Link to="/login" className="inline-flex items-center gap-1 text-sm text-emerald-700 hover:underline" data-testid="back-to-login">
            <ArrowLeft size={14} /> Kembali ke halaman masuk
          </Link>
        </div>
      </div>
    </div>
  );
}
