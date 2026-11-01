import React from "react";
import {
  Users,
  BookOpen,
  CheckCircle2,
  ShieldCheck,
  ArrowUpRight,
  Filter,
} from "lucide-react";

const mockRecentSessions = [
  {
    sessionId: "SES-A94F12",
    subjectCode: "CS401",
    subjectName: "Advanced Distributed Systems",
    cohort: "B.Tech CSE - Final Year (Sec A)",
    faculty: "Dr. K. Srinivas",
    conductedUnits: 2,
    presentCount: 42,
    totalEnrolled: 45,
    attendancePercent: "93.3%",
    receiptHash: "0x8fa1b9204c3e77a1",
    timestamp: "Today, 10:45 AM",
  },
  {
    sessionId: "SES-B18D44",
    subjectCode: "CS302",
    subjectName: "Database Engineering (Joint)",
    cohort: "Union: Sec A + Sec B",
    faculty: "Prof. P. Radhika",
    conductedUnits: 3,
    presentCount: 81,
    totalEnrolled: 88,
    attendancePercent: "92.0%",
    receiptHash: "0x331df89c2049ba01",
    timestamp: "Today, 11:30 AM",
  },
  {
    sessionId: "SES-C55E89",
    subjectCode: "EC204",
    subjectName: "Digital Signal Processing",
    cohort: "B.Tech ECE - 2nd Year",
    faculty: "Dr. M. Venkat",
    conductedUnits: 1,
    presentCount: 56,
    totalEnrolled: 60,
    attendancePercent: "93.3%",
    receiptHash: "0x9847ea0101bcae52",
    timestamp: "Today, 02:15 PM",
  },
];

export default function AdminDashboardPage() {
  return (
    <div className="space-y-8">
      {/* Page Title & Breadcrumb */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-bold text-institutional-navy">
            Executive Attendance Overview
          </h1>
          <p className="text-sm text-institutional-muted">
            Campus-wide attendance ledger, active academic offerings, and audit integrity.
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            type="button"
            className="inline-flex items-center space-x-2 px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium bg-white text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <Filter className="w-4 h-4 text-slate-500" />
            <span>Filter Term</span>
          </button>
          <button
            type="button"
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium bg-institutional-navy text-white hover:bg-institutional-navy/90 transition-colors"
          >
            <span>Live Audit Snapshot</span>
            <ArrowUpRight className="w-4 h-4" />
          </button>
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
            <div className="text-3xl font-bold text-slate-900 font-serif">1,420</div>
            <div className="text-xs text-slate-500 mt-1">Across 8 Cohorts & 4 Depts</div>
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
            <div className="text-3xl font-bold text-slate-900 font-serif">38</div>
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
            <div className="text-3xl font-bold text-slate-900 font-serif">14</div>
            <div className="text-xs text-emerald-600 font-medium mt-1">
              31 Conducted Units Today
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
            <div className="text-3xl font-bold text-teal-700 font-serif">100%</div>
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
          <h2 className="font-serif text-lg font-bold text-slate-900">
            Recent Committed Sessions
          </h2>
          <span className="text-xs font-medium text-slate-500">
            Showing last 3 recorded sessions
          </span>
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
              {mockRecentSessions.map((row) => (
                <tr key={row.sessionId} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-6 py-4 font-mono font-medium text-xs text-institutional-navy">
                    {row.sessionId}
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-medium text-slate-900">{row.subjectName}</div>
                    <div className="text-xs text-slate-500">
                      {row.subjectCode} • {row.cohort}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-700">{row.faculty}</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800">
                      {row.conductedUnits} Units
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-700 font-mono text-xs">
                    {row.presentCount} / {row.totalEnrolled}
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-semibold text-emerald-700">
                      {row.attendancePercent}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono text-xs text-slate-500">
                    {row.receiptHash}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

