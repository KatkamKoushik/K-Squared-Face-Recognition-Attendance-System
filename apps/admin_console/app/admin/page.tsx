"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Users,
  BookOpen,
  CheckCircle2,
  ShieldCheck,
  ShieldAlert,
  ArrowUpRight,
  Filter,
  Activity,
  FileCheck2,
  Building2,
  RefreshCw,
  Lock,
  Mail,
  AlertCircle,
  Eye,
} from "lucide-react";
import {
  getAuthToken,
  getStoredUser,
  login,
  getAdminDashboardMetrics,
  AdminDashboardMetrics,
  StoredAuthUser,
} from "@/lib/api";

export default function AdminDashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<StoredAuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  // Login form state (if not authenticated)
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  // Live dashboard data
  const [metrics, setMetrics] = useState<AdminDashboardMetrics | null>(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [metricsError, setMetricsError] = useState<string | null>(null);

  useEffect(() => {
    const t = getAuthToken();
    const u = getStoredUser();
    setToken(t);
    setUser(u);
    setCheckingAuth(false);

    if (t && u) {
      loadLiveMetrics();
    }
  }, []);

  const loadLiveMetrics = async () => {
    setLoadingMetrics(true);
    setMetricsError(null);
    try {
      const data = await getAdminDashboardMetrics();
      if (data) {
        setMetrics(data);
      } else {
        setMetricsError("Failed to fetch live database metrics from FastAPI control plane.");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error contacting backend control plane.";
      setMetricsError(msg);
    } finally {
      setLoadingMetrics(false);
    }
  };

  const handleAdminLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginEmail.trim() || !loginPassword.trim()) {
      setLoginError("Please enter your administrator email and password.");
      return;
    }

    setLoginLoading(true);
    setLoginError(null);

    try {
      const res = await login(loginEmail.trim(), loginPassword, true);
      if (res && res.access_token) {
        setToken(res.access_token);
        setUser({
          user_id: res.user_id,
          email: res.email,
          role: res.role,
        });
        loadLiveMetrics();
      } else {
        setLoginError("Invalid administrator credentials or insufficient permissions.");
      }
    } catch {
      setLoginError("Unable to connect to FastAPI control plane. Ensure backend service is running.");
    } finally {
      setLoginLoading(false);
    }
  };

  if (checkingAuth) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="flex items-center space-x-2 text-slate-500 text-sm">
          <RefreshCw className="w-4 h-4 animate-spin text-institutional-navy" />
          <span>Verifying administrative authorization...</span>
        </div>
      </div>
    );
  }

  // Not authenticated: render real administrator login interface
  if (!token || !user) {
    return (
      <div className="max-w-md mx-auto py-12 px-4">
        <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-xl space-y-6">
          <div className="text-center">
            <div className="mx-auto w-12 h-12 rounded-xl bg-institutional-navy flex items-center justify-center text-white font-serif font-bold text-xl shadow-md">
              K²
            </div>
            <h1 className="mt-4 font-serif text-2xl font-bold tracking-tight text-institutional-navy">
              Administrator Authentication
            </h1>
            <p className="mt-1 text-xs text-slate-500">
              Kakatiya University College of Engineering & Technology
            </p>
            <div className="mt-2 inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
              <ShieldCheck className="w-3.5 h-3.5 text-institutional-blue" />
              <span>Server-Side Role & Resource Authorization</span>
            </div>
          </div>

          {loginError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
              <span>{loginError}</span>
            </div>
          )}

          <form onSubmit={handleAdminLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Institutional Admin Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
                <input
                  type="email"
                  required
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  placeholder="admin@kucet.ac.in"
                  className="w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-hidden focus:ring-2 focus:ring-institutional-navy focus:bg-white transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
                <input
                  type="password"
                  required
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-hidden focus:ring-2 focus:ring-institutional-navy focus:bg-white transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loginLoading}
              className="w-full py-2.5 px-4 bg-institutional-navy text-white rounded-xl text-sm font-semibold hover:bg-institutional-navy/90 disabled:opacity-50 transition-all shadow-md cursor-pointer flex items-center justify-center space-x-2"
            >
              {loginLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <span>Access Protected Console</span>
              )}
            </button>
          </form>

          <div className="pt-2 text-center">
            <Link
              href="/"
              className="text-xs text-institutional-blue hover:text-institutional-navy font-medium underline"
            >
              Return to Public Student Enrollment Portal
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Authenticated: Render real database-backed dashboard
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl font-bold text-institutional-navy">
            Executive Attendance & Biometric Control Plane
          </h1>
          <p className="text-sm text-slate-500">
            Authoritative PostgreSQL ledger, student biometric verification queue, and academic structure.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={loadLiveMetrics}
            disabled={loadingMetrics}
            className="inline-flex items-center space-x-2 px-3 py-2 border border-slate-300 rounded-lg text-xs font-semibold bg-white text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${loadingMetrics ? "animate-spin" : ""}`} />
            <span>Refresh Telemetry</span>
          </button>
          <Link
            href="/admin/enrollment"
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold bg-institutional-navy text-white hover:bg-institutional-navy/90 transition-colors shadow-sm"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
            <span>Review Pending Enrollments</span>
          </Link>
        </div>
      </div>

      {metricsError && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Notice:</span> {metricsError}
          </div>
        </div>
      )}

      {/* Live Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Enrolled Students */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Total Enrolled Students
            </span>
            <Users className="w-5 h-5 text-institutional-blue" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold text-slate-900 font-serif">
              {metrics ? metrics.total_enrolled_students : "—"}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Active in institutional database
            </div>
          </div>
        </div>

        {/* Pending Biometric Submissions */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Pending Enrollment Queue
            </span>
            <ShieldAlert className="w-5 h-5 text-amber-500" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold text-slate-900 font-serif">
              {metrics ? metrics.pending_submissions_count : "—"}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Awaiting admin verification & template generation
            </div>
          </div>
        </div>

        {/* Active Subject Offerings */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Active Subject Offerings
            </span>
            <BookOpen className="w-5 h-5 text-institutional-navy" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold text-slate-900 font-serif">
              {metrics ? metrics.total_active_offerings : "—"}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Registered academic course units
            </div>
          </div>
        </div>

        {/* Finalized Sessions */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Finalized Sessions
            </span>
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold text-slate-900 font-serif">
              {metrics ? metrics.finalized_sessions_count : "—"}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Durable commit receipts anchored
            </div>
          </div>
        </div>
      </div>

      {/* Quick Action Portals */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          href="/admin/enrollment"
          className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:border-institutional-navy hover:shadow-md transition-all group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-slate-400 group-hover:text-institutional-navy transition-colors" />
          </div>
          <h2 className="font-serif font-bold text-base text-slate-900 group-hover:text-institutional-navy transition-colors">
            Biometric Enrollment Review
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Inspect submitted student portraits, verify academic roll numbers, approve templates, or request recapture.
          </p>
        </Link>

        <Link
          href="/students"
          className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:border-institutional-navy hover:shadow-md transition-all group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 text-institutional-blue flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-slate-400 group-hover:text-institutional-navy transition-colors" />
          </div>
          <h2 className="font-serif font-bold text-base text-slate-900 group-hover:text-institutional-navy transition-colors">
            Student Directory
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Browse registered student profiles, verify active facial template status, and manage cohort enrollments.
          </p>
        </Link>

        <Link
          href="/audit/logs"
          className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:border-institutional-navy hover:shadow-md transition-all group"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <FileCheck2 className="w-5 h-5" />
            </div>
            <ArrowUpRight className="w-4 h-4 text-slate-400 group-hover:text-institutional-navy transition-colors" />
          </div>
          <h2 className="font-serif font-bold text-base text-slate-900 group-hover:text-institutional-navy transition-colors">
            Authoritative Audit Trail
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Inspect append-only audit events, commit receipts, and biometric governance state transitions.
          </p>
        </Link>
      </div>

      {/* Operational Infrastructure Status */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-institutional-navy" />
            <h2 className="font-serif font-bold text-sm text-slate-900">
              System Infrastructure & Vision Model Readiness
            </h2>
          </div>
          <Link
            href="/system/readiness"
            className="text-xs font-semibold text-institutional-blue hover:text-institutional-navy"
          >
            Detailed Health Probe →
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <div className="text-slate-500 font-medium">Database Layer</div>
            <div className="text-sm font-bold text-emerald-700 mt-1 flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>PostgreSQL Connected</span>
            </div>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <div className="text-slate-500 font-medium">Vision Models</div>
            <div className="text-sm font-bold text-slate-900 mt-1">
              YuNet (2023mar) + SFace (2021dec)
            </div>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <div className="text-slate-500 font-medium">Inference Execution</div>
            <div className="text-sm font-bold text-slate-900 mt-1">
              Strict Fail-Closed Mode (STRICT=1)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
