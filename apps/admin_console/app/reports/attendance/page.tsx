"use client";

import React, { useState, useEffect } from "react";
import { Download, Filter, HelpCircle, AlertCircle, Database, FileSpreadsheet, RefreshCw } from "lucide-react";
import {
  getOfferingAnalytics,
  getOfferings,
  getOfferingAttendanceExportUrl,
  getOfferingAttendanceXlsxExportUrl,
  SubjectOfferingItem,
  OfferingAttendanceAnalytics,
} from "@/lib/api";

interface StudentReportRow {
  rollNumber: string;
  fullName: string;
  eligibleConductedUnits: number;
  attendedUnits: number;
  attendancePercent: number | null;
}

function calculateAttendancePercent(attended: number, conducted: number, rawPct: number | null): {
  display: string;
  isNa: boolean;
} {
  if (conducted === 0 || rawPct === null) {
    return { display: "N/A", isNa: true };
  }
  const pct = (100 * attended) / conducted;
  return { display: `${pct.toFixed(1)}%`, isNa: false };
}

export default function AttendanceReportsPage() {
  const [offerings, setOfferings] = useState<SubjectOfferingItem[]>([]);
  const [selectedOfferingId, setSelectedOfferingId] = useState<string>("OFF-CS401-2026");
  const [analytics, setAnalytics] = useState<OfferingAttendanceAnalytics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isLive, setIsLive] = useState<boolean>(false);

  useEffect(() => {
    async function initOfferings() {
      try {
        const offList = await getOfferings();
        if (offList && offList.length > 0) {
          setOfferings(offList);
          setSelectedOfferingId(offList[0].id);
        }
      } catch {
        // Fallback default kept
      }
    }
    initOfferings();
  }, []);

  useEffect(() => {
    async function loadAnalytics() {
      if (!selectedOfferingId) return;
      setLoading(true);
      try {
        const data = await getOfferingAnalytics(selectedOfferingId);
        setAnalytics(data);
        setIsLive(Boolean(data && data.student_stats && data.student_stats.length > 0));
      } catch {
        setIsLive(false);
      } finally {
        setLoading(false);
      }
    }
    loadAnalytics();
  }, [selectedOfferingId]);

  const rows: StudentReportRow[] = (analytics?.student_stats || []).map((s) => ({
    rollNumber: s.roll_number,
    fullName: s.full_name,
    eligibleConductedUnits: s.eligible_conducted_units,
    attendedUnits: s.attended_conducted_units,
    attendancePercent: s.attendance_percent ?? null,
  }));

  const eligibleCount = rows.filter((r) => r.attendancePercent !== null && r.attendancePercent >= 75.0).length;
  const condonationCount = rows.filter((r) => r.attendancePercent !== null && r.attendancePercent >= 65.0 && r.attendancePercent < 75.0).length;
  const detentionRiskCount = rows.filter((r) => r.attendancePercent !== null && r.attendancePercent < 65.0).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl font-bold text-institutional-navy">
            Attendance Ledger & Analytics
          </h1>
          <p className="text-sm text-institutional-muted">
            Institutional attendance computed per student per conducted instructional unit.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-full border bg-white shadow-xs">
            <Database className={`w-3.5 h-3.5 ${isLive ? "text-emerald-600" : "text-slate-400"}`} />
            <span className={isLive ? "text-emerald-700 font-mono" : "text-slate-600"}>
              {isLive ? "LIVE ANALYTICS ENGINE" : "ANALYTICS DATABASE"}
            </span>
          </div>
          <a
            href={getOfferingAttendanceExportUrl(selectedOfferingId)}
            download
            className="inline-flex items-center space-x-2 px-3.5 py-2 border border-slate-300 rounded-lg text-sm font-medium bg-white text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
          >
            <Download className="w-4 h-4 text-slate-500" />
            <span>Export CSV</span>
          </a>
          <a
            href={getOfferingAttendanceXlsxExportUrl(selectedOfferingId)}
            download
            className="inline-flex items-center space-x-2 px-3.5 py-2 border border-slate-300 rounded-lg text-sm font-medium bg-white text-emerald-700 hover:bg-emerald-50 transition-colors shadow-xs"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
            <span>Export Excel (.xlsx)</span>
          </a>
        </div>
      </div>

      {/* Target Offering Selection Filter & Summary Metrics */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3 flex-1">
          <Filter className="w-4 h-4 text-slate-400" />
          <div className="text-sm font-semibold text-slate-800">
            Selected Course Offering:
          </div>
          <select
            value={selectedOfferingId}
            onChange={(e) => setSelectedOfferingId(e.target.value)}
            className="text-sm border border-slate-300 rounded-lg px-3 py-1.5 bg-slate-50 text-slate-800 font-medium focus:outline-none focus:ring-1 focus:ring-institutional-navy max-w-md"
          >
            {offerings.length > 0 ? (
              offerings.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.subject_code} - {o.subject_name} ({o.cohort_name} Sec {o.section})
                </option>
              ))
            ) : (
              <>
                <option value="OFF-CS401-2026">
                  CS401 - Distributed Systems (B.Tech CSE Final Year Sec A)
                </option>
                <option value="OFF-CS302-2026">
                  CS302 - Database Systems (Joint CSE + IT)
                </option>
                <option value="OFF-EC204-2026">
                  EC204 - Digital Signal Processing (ECE Second Year)
                </option>
              </>
            )}
          </select>
        </div>
        <div className="flex items-center space-x-4 text-xs font-mono">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span className="text-slate-600">Eligible: <strong>{eligibleCount}</strong></span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span className="text-slate-600">Condonation: <strong>{condonationCount}</strong></span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
            <span className="text-slate-600">Shortage: <strong>{detentionRiskCount}</strong></span>
          </div>
        </div>
      </div>

      {/* Analytics Notice */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start space-x-3 text-xs text-amber-900">
        <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold">Authoritative Invariant Enforcement:</span> Late-enrolled
          students or lateral entry transfers with zero eligible conducted units evaluate to{" "}
          <code className="font-mono bg-amber-100 px-1 py-0.5 rounded">N/A</code> rather than{" "}
          <code className="font-mono bg-amber-100 px-1 py-0.5 rounded">0.0%</code> to prevent unfair
          hall ticket barring due to unconducted instructional units.
        </div>
      </div>

      {/* Student Attendance Register Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500 flex flex-col items-center justify-center space-y-3">
            <RefreshCw className="w-6 h-6 animate-spin text-institutional-navy" />
            <p className="text-sm">Calculating institutional attendance arithmetic...</p>
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-6 py-3">Roll Number</th>
                <th className="px-6 py-3">Student Name</th>
                <th className="px-6 py-3">Eligible Units</th>
                <th className="px-6 py-3">Attended Units</th>
                <th className="px-6 py-3">Attendance %</th>
                <th className="px-6 py-3">Institutional Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {rows.length > 0 ? (
                rows.map((row) => {
                  const result = calculateAttendancePercent(
                    row.attendedUnits,
                    row.eligibleConductedUnits,
                    row.attendancePercent
                  );

                  return (
                    <tr key={row.rollNumber} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-6 py-4 font-mono font-medium text-xs text-slate-900">
                        {row.rollNumber}
                      </td>
                      <td className="px-6 py-4 font-medium text-slate-900">
                        {row.fullName}
                      </td>
                      <td className="px-6 py-4 text-slate-700 font-mono text-xs">
                        {row.eligibleConductedUnits} Units
                      </td>
                      <td className="px-6 py-4 text-slate-700 font-mono text-xs">
                        {row.attendedUnits} Units
                      </td>
                      <td className="px-6 py-4">
                        {result.isNa ? (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded text-xs font-bold bg-slate-100 text-slate-600">
                            <span>N/A</span>
                            <HelpCircle className="w-3 h-3 text-slate-400" />
                          </span>
                        ) : (
                          <span
                            className={`font-mono font-bold text-sm ${
                              parseFloat(result.display) >= 75
                                ? "text-emerald-600"
                                : parseFloat(result.display) >= 65
                                ? "text-amber-600"
                                : "text-rose-600"
                            }`}
                          >
                            {result.display}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {result.isNa ? (
                          <span className="text-xs text-slate-400">No conducted units</span>
                        ) : parseFloat(result.display) >= 75 ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                            Eligible (≥75%)
                          </span>
                        ) : parseFloat(result.display) >= 65 ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
                            Condonation (65-74%)
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200">
                            Detention Risk (&lt;65%)
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                    No attendance records accumulated yet for this offering in the live database.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
