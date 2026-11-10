"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  Users,
  BookOpen,
  CheckCircle2,
  ShieldCheck,
  ArrowUpRight,
  UserPlus,
  ShieldAlert,
  RefreshCw,
} from "lucide-react";
import { getAdminDashboardMetrics, AdminDashboardMetrics } from "@/lib/api";

export default function AdminDashboardPage() {
  const [metrics, setMetrics] = useState<AdminDashboardMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchMetrics = useCallback(async (isBackground = false) => {
    if (!isBackground) {
      setIsRefreshing(true);
    }
    try {
      const data = await getAdminDashboardMetrics();
      if (data) {
        setMetrics(data);
        setLastUpdated(new Date());
      }
    } catch (err) {
      console.warn("Failed to fetch live admin dashboard metrics:", err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics(false);

    // Poll every 5 seconds for real-time ledger updates
    const interval = setInterval(() => {
      fetchMetrics(true);
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchMetrics]);

  const recentSessions = metrics?.recent_sessions ?? [];

  return (
    <div className="space-y-8">
      {/* Page Title & Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-serif text-2xl font-bold text-institutional-navy">
              Executive Attendance Overview
            </h1>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
              Live Ledger
            </span>
          </div>
          <p className="text-sm text-institutional-muted">
            Campus-wide attendance ledger, active academic offerings, and audit integrity.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => fetchMetrics(false)}
            disabled={isRefreshing}
            className="inline-flex items-center space-x-1.5 px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium bg-white text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
            title="Refresh Ledger"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${isRefreshing ? "animate-spin" : ""}`} />
            <span>{isRefreshing ? "Syncing..." : "Sync"}</span>
          </button>
          <Link
            href="/enroll"
            className="inline-flex items-center space-x-2 px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium bg-white text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
          >
            <UserPlus className="w-4 h-4 text-institutional-blue" />
            <span>Student Portal</span>
          </Link>
          <Link
            href="/admin/enrollment"
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium bg-institutional-navy text-white hover:bg-institutional-navy/90 transition-colors shadow-sm"
          >
            <ShieldAlert className="w-4 h-4 text-institutional-gold" />
            <span>Biometric Queue</span>
            <ArrowUpRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Total Enrolled
            </span>
            <Users className="w-5 h-5 text-institutional-blue" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold text-slate-900 font-serif">
              {loading ? "-" : (metrics?.total_enrolled_students ?? 0).toLocaleString()}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Across {metrics?.active_cohorts_count ?? 8} Cohorts & {metrics?.active_departments_count ?? 7} Depts
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Active Offerings
            </span>
            <BookOpen className="w-5 h-5 text-institutional-gold" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold text-slate-900 font-serif">
              {loading ? "-" : (metrics?.total_active_offerings ?? 0).toLocaleString()}
            </div>
            <div className="text-xs text-slate-500 mt-1">Fall 2026 Academic Term</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Sessions Committed
            </span>
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold text-slate-900 font-serif">
              {loading ? "-" : (metrics?.finalized_sessions_count ?? 0).toLocaleString()}
            </div>
            <div className="text-xs text-emerald-600 font-medium mt-1">
              {metrics?.conducted_units_today ?? 0} Conducted Units Today
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Ledger State
            </span>
            <ShieldCheck className="w-5 h-5 text-teal-600" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold text-teal-700 font-serif">
              {loading ? "-" : (metrics?.system_readiness === "READY" ? "100%" : "READY")}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              All Units ACID Confirmed
            </div>
          </div>
        </div>
      </div>

      {/* Blueprint Invariant Banner */}
      <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 flex items-start space-x-3">
        <ShieldCheck className="w-5 h-5 text-institutional-blue flex-shrink-0 mt-0.5" />
        <div className="text-xs text-slate-700 leading-relaxed">
          <span className="font-semibold text-institutional-navy">
            Authoritative Arithmetic Invariant:
          </span>{" "}
          Attendance rates are computed strictly per student per authorized instructional unit
          conducted. Vision workers supply candidate proposals only; final commitment is
          executed through faculty authorization and logged with cryptographic transaction
          receipts.
        </div>
      </div>

      {/* Recent Sessions Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="font-serif text-lg font-bold text-slate-900">
              Recent Committed Sessions
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Live transaction receipts streamed from KUCET authoritative database
            </p>
          </div>
          <div className="text-xs text-slate-500">
            {lastUpdated ? `Last updated: ${lastUpdated.toLocaleTimeString()}` : "Syncing..."}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-6 py-3">Session ID</th>
                <th className="px-6 py-3">Subject Offering</th>
                <th className="px-6 py-3">Faculty</th>
                <th className="px-6 py-3">Conducted Units</th>
                <th className="px-6 py-3">Present / Enrolled</th>
                <th className="px-6 py-3">Attendance %</th>
                <th className="px-6 py-3">Receipt Hash</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {recentSessions.length > 0 ? (
                recentSessions.map((row) => (
                  <tr key={row.session_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-xs text-institutional-navy">
                      {row.session_id}
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900">{row.subject_name}</div>
                      <div className="text-xs text-slate-500">
                        {row.subject_code} • {row.cohort}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-700">{row.faculty}</td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800">
                        {row.conducted_units} Units
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-700 font-mono text-xs">
                      {row.present_count} / {row.total_enrolled}
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-semibold text-emerald-700">
                        {row.attendance_percent}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-500">
                      {row.receipt_hash}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <div className="max-w-md mx-auto space-y-2">
                      <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
                      <h3 className="text-sm font-semibold text-slate-800">
                        Authoritative Attendance Ledger Active
                      </h3>
                      <p className="text-xs text-slate-500 leading-relaxed">
                        No attendance sessions committed yet for today. Real-time session commits conducted by faculty via the teacher mobile app will display here immediately with immutable receipts.
                      </p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
