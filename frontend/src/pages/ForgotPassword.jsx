import React, { useState } from "react";
import { Link } from "react-router-dom";
import api, { apiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Moon, Loader2, ArrowLeft, CheckCircle2 } from "lucide-react";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true); setError("");
    try {
      await api.post("/auth/forgot-password", { email: email.trim() });
      setSent(true);
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
        {sent ? (
          <div className="text-center rounded-lg border border-slate-200 bg-white p-6" data-testid="forgot-success">
            <CheckCircle2 className="mx-auto text-emerald-600 mb-3" size={32} />
            <p className="font-heading font-semibold text-slate-800">Periksa Email Anda</p>
            <p className="text-sm text-slate-500 mt-1">Jika email terdaftar, tautan reset telah dikirim.</p>
          </div>
        ) : (
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <h2 className="font-heading text-xl font-bold text-emerald-950">Lupa Password</h2>
            <p className="text-sm text-slate-500 mt-1 mb-5">Masukkan email Anda untuk menerima tautan reset.</p>
            {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
            <form onSubmit={submit} className="space-y-4">
              <div>
                <Label className="text-sm text-slate-700 mb-1.5 block">Email</Label>
                <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
                  className="border-slate-200" data-testid="forgot-email" />
              </div>
              <Button type="submit" disabled={loading} className="w-full bg-emerald-900 hover:bg-emerald-800" data-testid="forgot-submit">
                {loading && <Loader2 size={16} className="mr-2 animate-spin" />} Kirim Tautan
              </Button>
            </form>
          </div>
        )}
        <div className="mt-4 text-center">
          <Link to="/login" className="inline-flex items-center gap-1 text-sm text-emerald-700 hover:underline" data-testid="back-to-login">
            <ArrowLeft size={14} /> Kembali ke halaman masuk
          </Link>
        </div>
      </div>
    </div>
  );
}
