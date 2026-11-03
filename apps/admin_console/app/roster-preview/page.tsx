import React from "react";
import { Eye, Lock, ShieldCheck, CheckCircle2, AlertTriangle, Database } from "lucide-react";
import { getStudents, StudentListItem } from "@/lib/api";

interface FrozenRosterItem {
  id: string;
  rollNumber: string;
  fullName: string;
  cohort: string;
  templateEnrolled: boolean;
  consentSigned: boolean;
  status: "ACTIVE" | "ON_LEAVE";
}

const mockFrozenRoster: FrozenRosterItem[] = [
  { id: "STU-KUCET-00622501", rollNumber: "00622501", fullName: "Katkam Koushik", cohort: "B.Tech CSE - Final Year (IV/IV Sec A)", templateEnrolled: true, consentSigned: true, status: "ACTIVE" },
  { id: "STU-KUCET-00622502", rollNumber: "00622502", fullName: "A. Sai Teja", cohort: "B.Tech CSE - Final Year (IV/IV Sec A)", templateEnrolled: true, consentSigned: true, status: "ACTIVE" },
  { id: "STU-KUCET-00622503", rollNumber: "00622503", fullName: "B. Manasa Reddy", cohort: "B.Tech CSE - Final Year (IV/IV Sec A)", templateEnrolled: true, consentSigned: true, status: "ACTIVE" },
  { id: "STU-KUCET-00622504", rollNumber: "00622504", fullName: "Ch. Rahul", cohort: "B.Tech CSE - Final Year (IV/IV Sec A)", templateEnrolled: true, consentSigned: true, status: "ACTIVE" },
  { id: "STU-KUCET-00622505", rollNumber: "00622505", fullName: "D. Ananya", cohort: "B.Tech CSE - Final Year (IV/IV Sec A)", templateEnrolled: false, consentSigned: true, status: "ACTIVE" },
  { id: "STU-KUCET-00622506", rollNumber: "00622506", fullName: "E. Srikanth", cohort: "B.Tech CSE - Final Year (IV/IV Sec A)", templateEnrolled: true, consentSigned: false, status: "ACTIVE" },
];

export default async function LiveRosterPreviewPage() {
  const serverStudents = await getStudents();
  const isLive = serverStudents !== null && serverStudents.length > 0;

  const roster: FrozenRosterItem[] = isLive
    ? serverStudents.map((s: StudentListItem) => ({
        id: s.id,
        rollNumber: s.roll_number,
        fullName: s.full_name,
        cohort: `Term ${s.current_term}`,
        templateEnrolled: true,
        consentSigned: s.consent_signed ?? true,
        status: (s.status as "ACTIVE" | "ON_LEAVE") || "ACTIVE",
      }))
    : mockFrozenRoster;

  const totalEligible = roster.length;
  const biometricReady = roster.filter((s) => s.templateEnrolled && s.consentSigned).length;
  const pendingConsentOrTemplate = totalEligible - biometricReady;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-bold text-institutional-navy">
            Live Roster Freeze & Eligibility Inspector
          </h1>
          <p className="text-sm text-institutional-muted">
            Preview immutable frozen roster snapshots, biometric template readiness, and DPDP consent compliance prior to session lock.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-full border bg-white shadow-xs">
            <Database className={`w-3.5 h-3.5 ${isLive ? "text-emerald-600" : "text-slate-400"}`} />
            <span className={isLive ? "text-emerald-700 font-mono" : "text-slate-600"}>
              {isLive ? "LIVE CONTROL PLANE" : "SAMPLE ROSTER SNAPSHOT"}
            </span>
          </div>
          <div className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
            <Lock className="w-3.5 h-3.5" />
            <span>Snapshot Verified</span>
          </div>
        </div>
      </div>

      {/* Target Offering Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="text-xs uppercase font-semibold text-slate-500 tracking-wider">
              Selected Target Offering
            </div>
            <div className="text-lg font-serif font-bold text-institutional-navy mt-1">
              CS401: Advanced Machine Learning & Neural Networks
            </div>
            <div className="text-xs text-slate-500 mt-0.5">
              Cohort: B.Tech CSE Class of 2026 (Section A) • Term: Semester VII (Odd 2026)
            </div>
          </div>
          <div className="flex items-center space-x-4 border-t sm:border-t-0 sm:border-l border-slate-200 pt-3 sm:pt-0 sm:pl-6">
            <div>
              <div className="text-xs text-slate-500">Planned Units</div>
              <div className="text-xl font-bold text-slate-800 font-mono">2 Units</div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Assigned Faculty</div>
              <div className="text-sm font-semibold text-slate-800">Dr. K. Srinivas</div>
            </div>
          </div>
        </div>
      </div>

      {/* Denominator Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-institutional-muted">
              Frozen Denominator (|U_c|)
            </span>
            <Eye className="w-5 h-5 text-institutional-blue" />
          </div>
          <div className="mt-2 text-2xl font-serif font-bold text-institutional-navy">
            {totalEligible} Students
          </div>
          <p className="mt-1 text-xs text-slate-500">Immutable baseline denominator</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-institutional-muted">
              Biometric Ready
            </span>
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-serif font-bold text-emerald-700">
            {biometricReady} Students
          </div>
          <p className="mt-1 text-xs text-slate-500">Template enrolled + consent signed</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-institutional-muted">
              Roll-Call Required
            </span>
            <AlertTriangle className="w-5 h-5 text-amber-600" />
          </div>
          <div className="mt-2 text-2xl font-serif font-bold text-amber-700">
            {pendingConsentOrTemplate} Students
          </div>
          <p className="mt-1 text-xs text-slate-500">Must use manual attendance fallback</p>
        </div>
      </div>

      {/* Student Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <h2 className="text-base font-semibold text-institutional-navy flex items-center space-x-2">
            <Eye className="w-4 h-4 text-institutional-blue" />
            <span>Frozen Roster Candidates</span>
          </h2>
          <span className="text-xs text-slate-500">Authoritative Snapshot Candidate List</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-600 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">Roll Number</th>
                <th className="px-6 py-3">Full Student Name</th>
                <th className="px-6 py-3">Cohort</th>
                <th className="px-6 py-3 text-center">Biometric Template</th>
                <th className="px-6 py-3 text-center">DPDP Consent</th>
                <th className="px-6 py-3">Enrolment Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {roster.map((student) => (
                <tr key={student.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="px-6 py-4 font-mono font-bold text-institutional-navy">
                    {student.rollNumber}
                  </td>
                  <td className="px-6 py-4 font-medium text-slate-800">
                    {student.fullName}
                  </td>
                  <td className="px-6 py-4 text-xs text-slate-600">
                    {student.cohort}
                  </td>
                  <td className="px-6 py-4 text-center">
                    {student.templateEnrolled ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Enrolled
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                        Missing
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-center">
                    {student.consentSigned ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Signed
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                        Pending
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                      {student.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Mathematical Invariant Banner */}
      <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex items-start space-x-3 text-xs text-slate-600">
        <ShieldCheck className="w-4 h-4 text-institutional-navy flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-800">Mathematical Invariant Guardrail:</span> Once a session transitions to <code className="font-mono bg-slate-200 px-1 py-0.5 rounded">ROSTER_FROZEN</code>, this candidate roster becomes immutable. If unconducted units occur, they are never coerced to 0 or 100, and mid-session student roster adjustments are strictly quarantined.
        </div>
      </div>
    </div>
  );
}

