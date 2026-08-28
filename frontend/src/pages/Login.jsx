import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { apiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Moon, Loader2, AlertCircle } from "lucide-react";
import { Link } from "react-router-dom";

const BG = "https://images.unsplash.com/photo-1602128110234-2d11c0aaadfe?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA0MTJ8MHwxfHNlYXJjaHwzfHxtb2Rlcm4lMjBtb3NxdWUlMjBtaW5pbWFsJTIwYXJjaGl0ZWN0dXJlfGVufDB8fHx8MTc4Nzg4Mzg3M3ww&ixlib=rb-4.1.0&q=85";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      await login(email.trim(), password);
      nav("/");
    } catch (err) {
      setError(apiError(err.response?.data?.detail) || "Gagal masuk.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-emerald-950">
      <div className="relative hidden lg:block">
        <img src={BG} alt="Arsitektur masjid" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-emerald-950/70" />
        <div className="relative z-10 flex flex-col justify-between h-full p-12 text-white">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-amber-500 text-emerald-950">
              <Moon size={22} fill="currentColor" />
            </div>
            <span className="font-heading font-extrabold text-xl tracking-tight">SIMPESRA LIM</span>
          </div>
          <div>
            <h1 className="font-heading text-4xl font-bold leading-tight">Sistem Informasi Monitoring Pesantren Ramadan</h1>
            <p className="mt-4 text-emerald-200 max-w-md">Lembaga Ittihadul Muballighin — pengelolaan dan pemantauan pelaksanaan kegiatan secara terstruktur.</p>
          </div>
          <p className="text-xs text-emerald-300/70">Aplikasi mengikuti kebutuhan organisasi.</p>
        </div>
      </div>

      <div className="flex items-center justify-center p-6 bg-slate-50">
        <div className="w-full max-w-sm">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-emerald-900 text-white">
              <Moon size={22} fill="currentColor" />
            </div>
            <span className="font-heading font-extrabold text-xl tracking-tight text-emerald-950">SIMPESRA LIM</span>
          </div>
          <h2 className="font-heading text-2xl font-bold text-emerald-950">Selamat Datang</h2>
          <p className="text-sm text-slate-500 mt-1 mb-6">Masuk untuk melanjutkan ke dashboard.</p>

          {error && (
            <div className="flex items-center gap-2 rounded-md bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2 mb-4" data-testid="login-error">
              <AlertCircle size={16} /> {error}
            </div>
          )}

          <form onSubmit={submit} className="space-y-4">
            <div>
              <Label className="text-sm text-slate-700 mb-1.5 block">Email</Label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required
                placeholder="nama@email.com" className="border-slate-200" data-testid="login-email" />
            </div>
            <div>
              <Label className="text-sm text-slate-700 mb-1.5 block">Password</Label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required
                placeholder="••••••••" className="border-slate-200" data-testid="login-password" />
            </div>
            <Button type="submit" disabled={loading} className="w-full bg-emerald-900 hover:bg-emerald-800" data-testid="login-submit">
              {loading && <Loader2 size={16} className="mr-2 animate-spin" />} Masuk
            </Button>
          </form>
          <div className="mt-4 text-center">
            <Link to="/forgot-password" className="text-sm text-emerald-700 hover:underline" data-testid="forgot-link">
              Lupa password?
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
