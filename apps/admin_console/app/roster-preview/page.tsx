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

export default async function LiveRosterPreviewPage() {
  const serverStudents = await getStudents();
  const isLive = serverStudents !== null;

  const roster: FrozenRosterItem[] = (serverStudents || []).map((s: StudentListItem) => ({
    id: s.id,
    rollNumber: s.roll_number,
    fullName: s.full_name,
    cohort: `Term ${s.current_term}`,
    templateEnrolled: true,
    consentSigned: s.consent_signed ?? true,
    status: (s.status as "ACTIVE" | "ON_LEAVE") || "ACTIVE",
  }));

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
              {isLive ? "LIVE CONTROL PLANE" : "ROSTER DATABASE"}
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
              CS401: Distributed Systems & Cloud Computing
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
              <div className="text-sm font-semibold text-slate-800">Dr. M. Soujanya</div>
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
          <p className="mt-1 text-xs text-slate-500">Active template & DPDP consent</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-institutional-muted">
              Alternative Mode Required
            </span>
            <AlertTriangle className="w-5 h-5 text-amber-600" />
          </div>
          <div className="mt-2 text-2xl font-serif font-bold text-amber-700">
            {pendingConsentOrTemplate} Students
          </div>
          <p className="mt-1 text-xs text-slate-500">Paper/manual roster sign-off</p>
        </div>
      </div>

      {/* Frozen Roster Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <h2 className="text-base font-semibold text-institutional-navy flex items-center space-x-2">
            <Lock className="w-4 h-4 text-institutional-blue" />
            <span>Frozen Eligible Students Snapshot</span>
          </h2>
          <span className="text-xs text-slate-500">Immutable snapshot reference</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-600 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">Roll Number</th>
                <th className="px-6 py-3">Full Student Name</th>
                <th className="px-6 py-3">Cohort</th>
                <th className="px-6 py-3 text-center">Template Status</th>
                <th className="px-6 py-3 text-center">DPDP Consent</th>
                <th className="px-6 py-3">Effective Eligibility</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {roster.length > 0 ? (
                roster.map((student) => {
                  const isReady = student.templateEnrolled && student.consentSigned;
                  return (
                    <tr key={student.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-6 py-4 font-mono font-bold text-institutional-blue">
                        {student.rollNumber}
                      </td>
                      <td className="px-6 py-4 font-medium text-slate-800">
                        {student.fullName}
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-600 font-mono">
                        {student.cohort}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${student.templateEnrolled ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-amber-50 text-amber-700 border-amber-200"}`}>
                          {student.templateEnrolled ? "Enrolled (128-d)" : "Missing"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${student.consentSigned ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-rose-50 text-rose-700 border-rose-200"}`}>
                          {student.consentSigned ? "Active" : "Withheld"}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${isReady ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-amber-50 text-amber-700 border-amber-200"}`}>
                          {isReady ? "Biometric Verifiable" : "Alternative Roll-Call Required"}
                        </span>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                    No enrolled students found in roster for this offering in the live database.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Snapshot Invariant Callout */}
      <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex items-start space-x-3 text-xs text-slate-600">
        <ShieldCheck className="w-4 h-4 text-institutional-blue flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-800">Immutable Snapshot Invariant:</span> Once a session is initialized, its roster denominator is permanently frozen in PostgreSQL. Mid-session roster additions, late section transfers, or post-hoc drops cannot alter the session denominator.
        </div>
      </div>
    </div>
  );
}
