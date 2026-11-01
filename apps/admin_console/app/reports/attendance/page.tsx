import React from "react";
import { Download, Filter, HelpCircle, AlertCircle, Database } from "lucide-react";
import { getOfferingAnalytics } from "@/lib/api";

interface StudentReportRow {
  rollNumber: string;
  fullName: string;
  cohort: string;
  eligibleConductedUnits: number;
  attendedUnits: number;
}

const mockReportData: StudentReportRow[] = [
  {
    rollNumber: "00622501",
    fullName: "Katkam Koushik",
    cohort: "B.Tech CSE - Final Year (IV/IV)",
    eligibleConductedUnits: 28,
    attendedUnits: 27,
  },
  {
    rollNumber: "00622502",
    fullName: "A. Sai Teja",
    cohort: "B.Tech CSE - Final Year (IV/IV)",
    eligibleConductedUnits: 28,
    attendedUnits: 26,
  },
  {
    rollNumber: "00622503",
    fullName: "B. Manasa Reddy",
    cohort: "B.Tech CSE - Final Year (IV/IV)",
    eligibleConductedUnits: 28,
    attendedUnits: 25,
  },
  {
    rollNumber: "00622504",
    fullName: "Ch. Rahul",
    cohort: "B.Tech CSE - Final Year (IV/IV)",
    eligibleConductedUnits: 28,
    attendedUnits: 21,
  },
  {
    rollNumber: "00622566",
    fullName: "K. Tharun (Late Lateral Admission / No Conducted Units Yet)",
    cohort: "B.Tech CSE - Final Year (IV/IV)",
    eligibleConductedUnits: 0, // Zero denominator test case!
    attendedUnits: 0,
  },
];

function calculateAttendancePercent(attended: number, conducted: number): {
  display: string;
  isNa: boolean;
} {
  if (conducted === 0) {
    return { display: "N/A", isNa: true };
  }
  const pct = (100 * attended) / conducted;
  return { display: `${pct.toFixed(1)}%`, isNa: false };
}

export default async function AttendanceReportsPage() {
  const analytics = await getOfferingAnalytics("OFF-CS401-2026");
  const isLive = analytics !== null && analytics.student_stats && analytics.student_stats.length > 0;

  const rows: StudentReportRow[] = isLive
    ? analytics.student_stats.map((s) => ({
        rollNumber: s.roll_number,
        fullName: s.full_name,
        cohort: "B.Tech CSE - Final Year",
        eligibleConductedUnits: s.eligible_conducted_units,
        attendedUnits: s.attended_conducted_units,
      }))
    : mockReportData;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
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
              {isLive ? "LIVE ANALYTICS ENGINE" : "ANALYTICS SNAPSHOT"}
            </span>
          </div>
          <button
            type="button"
            className="inline-flex items-center space-x-2 px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium bg-white text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <Download className="w-4 h-4 text-slate-500" />
            <span>Export Official Register (CSV)</span>
          </button>
        </div>
      </div>

      {/* Denominator Rule Alert */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="text-xs text-amber-900 leading-relaxed">
          <span className="font-semibold">Denominator Guardrail:</span> When a student has zero
          eligible conducted instructional units during an evaluation period, attendance rate is
          strictly evaluated as <code className="bg-amber-100 px-1 py-0.5 rounded font-mono font-bold">N/A</code>,
          never coerced to 0% or 100%.
        </div>
      </div>

      {/* Reports Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="text-sm font-semibold text-slate-800">
            Student Attendance Roster
          </div>
          <div className="flex items-center space-x-2 text-xs text-slate-500">
            <Filter className="w-3.5 h-3.5" />
            <span>Cohort: B.Tech CSE Final Year (Fall 2026)</span>
          </div>
        </div>

        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-6 py-3">Roll Number</th>
              <th className="px-6 py-3">Student Name</th>
              <th className="px-6 py-3">Eligible Conducted Units</th>
              <th className="px-6 py-3">Attended Units</th>
              <th className="px-6 py-3">Attendance %</th>
              <th className="px-6 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {rows.map((row) => {
              const result = calculateAttendancePercent(
                row.attendedUnits,
                row.eligibleConductedUnits
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
                            : "text-amber-600"
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
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
                        Shortage (&lt;75%)
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
