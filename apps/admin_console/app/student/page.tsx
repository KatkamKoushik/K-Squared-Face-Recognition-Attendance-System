"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  GraduationCap,
  BookOpen,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Send,
  LogOut,
  ChevronRight,
  Shield,
  FileText,
  UserCheck,
} from "lucide-react";
import {
  getStudentProfile,
  getStudentAttendanceSummary,
  getStudentOfferingLedger,
  getStudentAppeals,
  submitStudentAppeal,
  setAuthToken,
  setStoredUser,
  StudentProfile,
  StudentAttendanceItem,
  AttendanceAppealItem,
} from "@/lib/api";

export default function StudentDashboardPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [attendance, setAttendance] = useState<StudentAttendanceItem[]>([]);
  const [appeals, setAppeals] = useState<AttendanceAppealItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Active Ledger Modal State
  const [selectedOffering, setSelectedOffering] = useState<StudentAttendanceItem | null>(null);
  const [ledgerData, setLedgerData] = useState<any | null>(null);
  const [ledgerLoading, setLedgerLoading] = useState(false);

  // Appeal Submission State
  const [appealModal, setAppealModal] = useState<{
    sessionId: string;
    unitId: string;
    unitIndex: number;
    sessionDate: string;
  } | null>(null);
  const [appealReason, setAppealReason] = useState("");
  const [submittingAppeal, setSubmittingAppeal] = useState(false);
  const [appealSuccessMsg, setAppealSuccessMsg] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<"courses" | "appeals">("courses");

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [profData, attData, appData] = await Promise.all([
        getStudentProfile(),
        getStudentAttendanceSummary(),
        getStudentAppeals(),
      ]);

      if (!profData) {
        router.push("/student/login");
        return;
      }

      setProfile(profData);
      setAttendance(attData || []);
      setAppeals(appData || []);
    } catch (err: any) {
      setError(err?.message || "Failed to load student attendance dashboard.");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenLedger = async (item: StudentAttendanceItem) => {
    setSelectedOffering(item);
    setLedgerLoading(true);
    setAppealSuccessMsg(null);
    try {
      const ledger = await getStudentOfferingLedger(item.offering_id);
      setLedgerData(ledger);
    } catch (err: any) {
      alert("Failed to fetch session ledger: " + err.message);
    } finally {
      setLedgerLoading(false);
    }
  };

  const handleOpenAppealModal = (sessionId: string, unitId: string, unitIndex: number, sessionDate: string) => {
    setAppealModal({ sessionId, unitId, unitIndex, sessionDate });
    setAppealReason("");
    setAppealSuccessMsg(null);
  };

  const handleSubmitAppeal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!appealModal) return;
    setSubmittingAppeal(true);
    try {
      await submitStudentAppeal(appealModal.sessionId, appealModal.unitId, appealReason);
      setAppealSuccessMsg("Appeal submitted successfully. Awaiting administrative review.");
      setAppealModal(null);
      // Reload appeals list
      const updatedAppeals = await getStudentAppeals();
      setAppeals(updatedAppeals || []);
    } catch (err: any) {
      alert("Failed to submit appeal: " + err.message);
    } finally {
      setSubmittingAppeal(false);
    }
  };

  const handleSignOut = () => {
    setAuthToken(null);
    setStoredUser(null);
    router.push("/student/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-institutional-navy border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-medium text-slate-600">Verifying student credentials and loading attendance records...</p>
        </div>
      </div>
    );
  }

  // Calculate Institutional Compliance Metrics
  const totalEligible = attendance.reduce((sum, item) => sum + item.eligible_conducted_units, 0);
  const totalAttended = attendance.reduce((sum, item) => sum + item.attended_conducted_units, 0);
  const overallPercentage = totalEligible > 0 ? ((totalAttended / totalEligible) * 100).toFixed(1) : null;

  return (
    <div className="min-h-screen bg-slate-50 pb-16">
      {/* Top Navigation Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-institutional-navy rounded-xl flex items-center justify-center shadow-xs">
              <GraduationCap className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <span className="font-serif font-bold text-base text-institutional-navy block leading-tight">
                KUCET Student Portal
              </span>
              <span className="text-xs text-slate-500">Attendance Dossier & Appeals</span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden sm:block text-right">
              <span className="text-xs font-semibold text-slate-800 block">{profile?.full_name}</span>
              <span className="text-xs font-mono text-slate-500">{profile?.roll_number}</span>
            </div>
            <button
              onClick={handleSignOut}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors border border-slate-200"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-6">
        {/* Profile Card Banner */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1.5">
            <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full text-xs font-semibold bg-sky-50 text-sky-800 border border-sky-200">
              <Shield className="w-3 h-3 text-sky-600" />
              <span>Authoritative Institutional Record</span>
            </div>
            <h1 className="text-2xl font-serif font-bold text-institutional-navy">
              Welcome back, {profile?.full_name}
            </h1>
            <p className="text-sm text-slate-600">
              {profile?.department_name} • {profile?.cohort_name} • Roll No:{" "}
              <span className="font-mono font-semibold text-slate-800">{profile?.roll_number}</span>
            </p>
          </div>

          {/* Aggregate Attendance Card */}
          <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 min-w-[240px] flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">
                Overall Attendance
              </span>
              <div className="mt-1 flex items-baseline space-x-2">
                <span className="text-3xl font-serif font-bold text-institutional-navy">
                  {overallPercentage !== null ? `${overallPercentage}%` : "N/A"}
                </span>
                <span className="text-xs text-slate-500">
                  ({totalAttended}/{totalEligible} Units)
                </span>
              </div>
            </div>
            <div
              className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-sm ${
                overallPercentage !== null && parseFloat(overallPercentage) >= 75.0
                  ? "bg-emerald-100 text-emerald-800"
                  : overallPercentage !== null && parseFloat(overallPercentage) >= 65.0
                  ? "bg-amber-100 text-amber-800"
                  : "bg-rose-100 text-rose-800"
              }`}
            >
              {overallPercentage !== null && parseFloat(overallPercentage) >= 75.0 ? (
                <CheckCircle2 className="w-6 h-6 text-emerald-600" />
              ) : (
                <AlertTriangle className="w-6 h-6 text-rose-600" />
              )}
            </div>
          </div>
        </div>

        {appealSuccessMsg && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center space-x-3 text-emerald-800 text-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span>{appealSuccessMsg}</span>
          </div>
        )}

        {/* Tab Selector */}
        <div className="flex border-b border-slate-200 space-x-6 text-sm font-semibold">
          <button
            onClick={() => setActiveTab("courses")}
            className={`pb-3 flex items-center space-x-2 border-b-2 transition-colors ${
              activeTab === "courses"
                ? "border-institutional-navy text-institutional-navy"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span>Enrolled Subjects ({attendance.length})</span>
          </button>
          <button
            onClick={() => setActiveTab("appeals")}
            className={`pb-3 flex items-center space-x-2 border-b-2 transition-colors ${
              activeTab === "appeals"
                ? "border-institutional-navy text-institutional-navy"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>My Attendance Appeals ({appeals.length})</span>
          </button>
        </div>

        {/* Courses Tab */}
        {activeTab === "courses" && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {attendance.map((item) => {
                const pct = item.attendance_percent;
                const isEligible = pct !== null && pct >= 75.0;
                const isCondonation = pct !== null && pct >= 65.0 && pct < 75.0;
                const isDetention = pct !== null && pct < 65.0;

                return (
                  <div
                    key={item.offering_id}
                    className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between hover:border-slate-300 transition-colors"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-xs px-2.5 py-1 rounded bg-slate-100 text-institutional-navy">
                          {item.subject_code} • Sec {item.section}
                        </span>
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                            isEligible
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : isCondonation
                              ? "bg-amber-50 text-amber-700 border border-amber-200"
                              : isDetention
                              ? "bg-rose-50 text-rose-700 border border-rose-200"
                              : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {item.eligibility_status.replace(/_/g, " ")}
                        </span>
                      </div>

                      <h3 className="mt-3 text-base font-semibold text-slate-900 leading-snug">
                        {item.subject_name}
                      </h3>

                      <div className="mt-4 flex items-baseline justify-between text-xs text-slate-500">
                        <span>Instructional Units:</span>
                        <span className="font-semibold text-slate-800">
                          {item.attended_conducted_units} attended / {item.eligible_conducted_units} conducted
                        </span>
                      </div>

                      {/* Visual Progress Bar */}
                      <div className="mt-2 w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            isEligible
                              ? "bg-emerald-500"
                              : isCondonation
                              ? "bg-amber-500"
                              : isDetention
                              ? "bg-rose-500"
                              : "bg-slate-300"
                          }`}
                          style={{ width: `${Math.min(pct ?? 0, 100)}%` }}
                        />
                      </div>
                    </div>

                    <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
                      <div className="text-xs">
                        <span className="text-slate-500">Current Percentage: </span>
                        <span className="font-serif font-bold text-base text-institutional-navy">
                          {pct !== null ? `${pct.toFixed(1)}%` : "N/A"}
                        </span>
                      </div>

                      <button
                        onClick={() => handleOpenLedger(item)}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-institutional-navy hover:text-white transition-colors"
                      >
                        <span>View Ledger</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {attendance.length === 0 && (
              <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500">
                <BookOpen className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                <p className="text-sm font-medium">No enrolled subjects found for current academic term.</p>
              </div>
            )}
          </div>
        )}

        {/* Appeals Tab */}
        {activeTab === "appeals" && (
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-institutional-navy flex items-center space-x-2">
                <FileText className="w-4 h-4 text-institutional-blue" />
                <span>Attendance Appeal Dossier</span>
              </h2>
              <span className="text-xs text-slate-500">Audited institutional corrections</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-600 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-3">Appeal ID</th>
                    <th className="px-6 py-3">Session Date / Unit</th>
                    <th className="px-6 py-3">Justification</th>
                    <th className="px-6 py-3">Review Outcome</th>
                    <th className="px-6 py-3">Submitted At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {appeals.length > 0 ? (
                    appeals.map((app) => (
                      <tr key={app.id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="px-6 py-4 font-mono text-xs text-slate-600">{app.id.substring(0, 8)}...</td>
                        <td className="px-6 py-4 font-mono text-xs text-institutional-blue">
                          Session {app.session_id.substring(0, 8)}...
                        </td>
                        <td className="px-6 py-4 text-xs text-slate-700 max-w-xs">{app.reason}</td>
                        <td className="px-6 py-4">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                              app.status === "APPROVED"
                                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                : app.status === "REJECTED"
                                ? "bg-rose-50 text-rose-700 border border-rose-200"
                                : "bg-amber-50 text-amber-700 border border-amber-200"
                            }`}
                          >
                            {app.status}
                          </span>
                          {app.review_notes && (
                            <span className="block text-xs text-slate-500 mt-1 italic">
                              "{app.review_notes}"
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-xs text-slate-500 font-mono">
                          {new Date(app.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="px-6 py-10 text-center text-slate-500 text-xs">
                        No appeals submitted yet. To appeal an absent record, open a subject ledger above and click "File Appeal".
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Ledger Modal */}
      {selectedOffering && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
              <div>
                <h3 className="font-semibold text-base text-institutional-navy">
                  {selectedOffering.subject_name} ({selectedOffering.subject_code})
                </h3>
                <p className="text-xs text-slate-500">
                  Granular session and unit ledger history for student {profile?.roll_number}
                </p>
              </div>
              <button
                onClick={() => setSelectedOffering(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 flex-1">
              {ledgerLoading ? (
                <div className="text-center py-8 text-xs text-slate-500">Loading sessions from ledger...</div>
              ) : ledgerData?.sessions?.length > 0 ? (
                ledgerData.sessions.map((sess: any) => (
                  <div key={sess.session_id} className="border border-slate-200 rounded-xl p-4 space-y-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-700 flex items-center space-x-1.5">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        <span>Date: {sess.session_date}</span>
                      </span>
                      <span className="font-mono text-slate-400">ID: {sess.session_id.substring(0, 12)}...</span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {sess.units.map((u: any) => {
                        const isPresent = u.status === "PRESENT_CONFIRMED";
                        const isExcused = u.status === "EXCUSED";
                        const isAbsent = u.status === "ABSENT_CONFIRMED";

                        return (
                          <div
                            key={u.unit_id}
                            className={`p-2.5 rounded-lg border text-xs flex items-center justify-between ${
                              isPresent
                                ? "bg-emerald-50/50 border-emerald-200 text-emerald-900"
                                : isExcused
                                ? "bg-sky-50/50 border-sky-200 text-sky-900"
                                : "bg-rose-50/50 border-rose-200 text-rose-900"
                            }`}
                          >
                            <span className="font-semibold">Unit {u.unit_index}</span>
                            <div className="flex items-center space-x-2">
                              <span className="font-medium text-[11px]">
                                {isPresent ? "Present" : isExcused ? "Excused" : "Absent"}
                              </span>
                              {isAbsent && (
                                <button
                                  onClick={() =>
                                    handleOpenAppealModal(sess.session_id, u.unit_id, u.unit_index, sess.session_date)
                                  }
                                  className="px-2 py-0.5 rounded bg-rose-600 text-white text-[10px] font-semibold hover:bg-rose-700 transition-colors"
                                >
                                  Appeal
                                </button>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-xs text-slate-500">No finalized sessions found for this subject.</div>
              )}
            </div>

            <div className="px-6 py-3 border-t border-slate-200 bg-slate-50/50 text-right">
              <button
                onClick={() => setSelectedOffering(null)}
                className="px-4 py-2 rounded-lg bg-slate-200 text-slate-800 text-xs font-semibold hover:bg-slate-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Appeal Submission Modal */}
      {appealModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
              <h3 className="font-semibold text-sm text-institutional-navy">Submit Attendance Appeal</h3>
              <button onClick={() => setAppealModal(null)} className="text-slate-400 hover:text-slate-700">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmitAppeal} className="p-6 space-y-4">
              <div className="text-xs text-slate-600 space-y-1">
                <div>
                  <span className="font-semibold">Session Date:</span> {appealModal.sessionDate}
                </div>
                <div>
                  <span className="font-semibold">Instructional Unit:</span> Unit {appealModal.unitIndex}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
                  Justification & Reason
                </label>
                <textarea
                  required
                  rows={4}
                  value={appealReason}
                  onChange={(e) => setAppealReason(e.target.value)}
                  placeholder="Provide detailed justification (e.g., medical leave with certificate, authorized university representation, symposium participation)..."
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-institutional-navy focus:border-institutional-navy"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setAppealModal(null)}
                  className="px-3.5 py-2 text-xs font-semibold rounded-lg text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingAppeal || appealReason.trim().length < 5}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-institutional-navy text-white hover:bg-institutional-navy/90 disabled:opacity-50 flex items-center space-x-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{submittingAppeal ? "Submitting..." : "Submit Appeal"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
