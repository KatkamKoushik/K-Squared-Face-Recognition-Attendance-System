"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ShieldCheck, Lock, Mail, AlertCircle, ArrowRight, CheckCircle2, Camera } from "lucide-react";
import { login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please enter both institutional email and password.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await login(email.trim(), password, remember);
      if (res && res.access_token) {
        setSuccess(true);
        setTimeout(() => {
          router.push("/");
        }, 600);
      } else {
        setError("Invalid institutional credentials or unauthorized role. Please verify your credentials.");
      }
    } catch (err) {
      setError("Unable to connect to FastAPI control plane. Ensure backend service is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex flex-col justify-center items-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 bg-white p-8 rounded-2xl border border-slate-200 shadow-xl">
        {/* Institutional Branding */}
        <div className="text-center">
          <div className="mx-auto w-12 h-12 rounded-xl bg-institutional-navy flex items-center justify-center text-white font-serif font-bold text-xl shadow-md">
            K²
          </div>
          <h2 className="mt-4 font-serif text-2xl font-bold tracking-tight text-institutional-navy">
            FRS Admin Console
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Kakatiya University College of Engineering & Technology
          </p>
          <div className="mt-2 inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
            <ShieldCheck className="w-3.5 h-3.5 text-institutional-blue" />
            <span>PostgreSQL Authoritative Control Plane</span>
          </div>
        </div>

        {/* Status Alerts */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-700 flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>Authentication verified. Redirecting to workspace...</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Institutional Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@kucet.ac.in"
                className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-institutional-blue focus:border-institutional-blue"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-institutional-blue focus:border-institutional-blue"
              />
            </div>
          </div>

          <div className="flex items-center justify-between text-xs">
            <label className="flex items-center space-x-2 text-slate-600 cursor-pointer">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="rounded border-slate-300 text-institutional-blue focus:ring-institutional-blue"
              />
              <span>Remember session</span>
            </label>
            <span className="text-slate-400">JWT Scoped</span>
          </div>

          <button
            type="submit"
            disabled={loading || success}
            className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-institutional-navy hover:bg-institutional-navy/90 text-white rounded-xl text-sm font-semibold transition-all shadow-md hover:shadow-lg disabled:opacity-50"
          >
            <span>{loading ? "Authenticating..." : "Sign In to Admin Console"}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="pt-4 border-t border-slate-200">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-left">
            <div className="flex items-center space-x-2 text-xs font-semibold text-institutional-navy">
              <Camera className="w-4 h-4 text-institutional-blue" />
              <span>Mode 2: Demo Testing & Face Visualizer</span>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              Universal sandbox for testing group photo recognition and ground-truth bounding box overlays across all enrolled students.
            </p>
            <Link
              href="/demo"
              className="mt-3 inline-flex items-center space-x-1.5 text-xs font-semibold text-institutional-blue hover:text-institutional-navy transition-colors"
            >
              <span>Launch Demo Visualizer</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
