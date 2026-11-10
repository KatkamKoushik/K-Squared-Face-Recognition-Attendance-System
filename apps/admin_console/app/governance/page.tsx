"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Trash2,
  KeyRound,
  Scale,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Database,
  FileCheck2,
  HardDrive,
  Users,
} from "lucide-react";
import {
  getGovernanceSummary,
  getStudents,
  executePurge,
  toggleBiometricConsent,
  verifyReceipt,
  GovernanceSummary,
  PurgeResult,
  ReceiptVerificationResult,
} from "@/lib/api";
export interface StudentConsentRow {
  studentId: string;
  rollNumber: string;
  fullName: string;
  biometricConsentActive: boolean;
  alternativeRollCallRequired: boolean;
}

export default function GovernancePage() {
  const [summary, setSummary] = useState<GovernanceSummary | null>(null);
  const [students, setStudents] = useState<StudentConsentRow[]>([]);
  const [isLiveBackend, setIsLiveBackend] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Purge state
  const [retentionDays, setRetentionDays] = useState<number>(7);
  const [purgeResult, setPurgeResult] = useState<PurgeResult | null>(null);
  const [purgeError, setPurgeError] = useState<string | null>(null);

  // Receipt verification state
  const [verifySessionId, setVerifySessionId] = useState<string>("SES-2026-CSE-401");
  const [receiptResult, setReceiptResult] = useState<ReceiptVerificationResult | null>(null);
  const [receiptLoading, setReceiptLoading] = useState<boolean>(false);
  const [receiptError, setReceiptError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [summaryRes, studentsRes] = await Promise.all([
        getGovernanceSummary(),
        getStudents(),
      ]);

      if (summaryRes) {
        setSummary(summaryRes);
      }

      if (studentsRes && studentsRes.length > 0) {
        setStudents(
          studentsRes.map((s) => ({
            studentId: s.id,
            rollNumber: s.roll_number,
            fullName: s.full_name,
            biometricConsentActive: s.consent_signed ?? true,
            alternativeRollCallRequired: !(s.consent_signed ?? true),
          }))
        );
        setIsLiveBackend(true);
      } else {
        setStudents([]);
        setIsLiveBackend(studentsRes !== null);
      }
    } catch {
      setIsLiveBackend(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleConsent = async (studentId: string, currentConsent: boolean) => {
    setActionLoading(studentId);
    try {
      const nextConsent = !currentConsent;
      const res = await toggleBiometricConsent(
        studentId,
        nextConsent,
        nextConsent
          ? "Biometric consent reinstated by student request"
          : "Biometric consent withheld; non-biometric alternative required",
      );

      setStudents((prev) =>
        prev.map((s) => {
          if (s.studentId === studentId) {
            return {
              ...s,
              biometricConsentActive: nextConsent,
              alternativeRollCallRequired: !nextConsent,
            };
          }
          return s;
        }),
      );

      // Refresh telemetry
      await loadData();
    } catch (err) {
      console.warn("Toggle consent error:", err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleExecutePurge = async () => {
    setActionLoading("purge");
    setPurgeError(null);
    setPurgeResult(null);
    try {
      const res = await executePurge(retentionDays);
      if (res) {
        setPurgeResult(res);
        await loadData();
      } else {
        setPurgeError("Purge request returned no result or server offline.");
      }
    } catch (err) {
      setPurgeError(String(err));
    } finally {
      setActionLoading(null);
    }
  };

  const handleVerifyReceipt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verifySessionId.trim()) return;
    setReceiptLoading(true);
    setReceiptError(null);
    setReceiptResult(null);
    try {
      const res = await verifyReceipt(verifySessionId.trim());
      if (res) {
        setReceiptResult(res);
      } else {
        setReceiptError("No cryptographically signed receipt found for this session ID in the database.");
      }
    } catch (err) {
      setReceiptError(String(err));
    } finally {
      setReceiptLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-bold text-institutional-navy">
            Data Governance, Biometric Privacy & Ephemeral Purging
          </h1>
          <p className="text-sm text-institutional-muted">
            Enforces non-biometric alternative workflows for students with withheld consent and physically unlinks raw classroom frames per institutional policy.
          </p>
        </div>
        <button
          type="button"
          onClick={loadData}
          disabled={loading}
          className="flex items-center space-x-2 text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 transition-colors shadow-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-institutional-blue" : "text-slate-600"}`} />
          <span>Refresh Governance State</span>
        </button>
      </div>

      {/* Live vs Offline Status Banner */}
      {!isLiveBackend ? (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center justify-between text-xs text-amber-900">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
            <div>
              <span className="font-semibold">Offline Preview Mode:</span> Control plane is unreachable or session token is absent. Showing local status.
            </div>
          </div>
          <button
            type="button"
            onClick={loadData}
            className="px-3 py-1 bg-amber-600 text-white rounded-md font-semibold hover:bg-amber-700 transition-colors shadow-xs"
          >
            Retry Connection
          </button>
        </div>
      ) : (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 flex items-center justify-between text-xs text-emerald-900">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="font-medium">Live Control Plane Connected: PostgreSQL authoritative consent records loaded.</span>
          </div>
          <span className="font-mono text-[11px] bg-white px-2 py-0.5 rounded border border-emerald-200">
            TLS / JWT Scoped
          </span>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Consent Compliance */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Biometric Consent Rate
            </span>
            <Scale className="w-4 h-4 text-institutional-blue" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold font-serif text-slate-900">
              {summary ? `${summary.consent_compliance_percentage.toFixed(1)}%` : "..."}
            </span>
            <span className="text-xs text-slate-500">compliant</span>
          </div>
          <div className="mt-2 text-xs text-slate-600 flex justify-between">
            <span>Active Consent: {summary?.students_with_biometric_consent ?? 0}</span>
            <span className="text-amber-700 font-semibold">
              Withheld: {summary?.students_withheld_consent ?? 0}
            </span>
          </div>
        </div>

        {/* Ephemeral Frame Storage */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Active Unpurged Frames
            </span>
            <HardDrive className="w-4 h-4 text-institutional-gold" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold font-serif text-slate-900">
              {summary ? summary.active_unpurged_frames : "..."}
            </span>
            <span className="text-xs text-slate-500">frames on disk</span>
          </div>
          <div className="mt-2 text-xs text-slate-600 flex justify-between">
            <span>Disk Footprint:</span>
            <span className="font-mono font-semibold">
              {summary ? `${summary.disk_usage_mb.toFixed(2)} MB` : "..."}
            </span>
          </div>
        </div>

        {/* Retention Policy */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Retention Mandate
            </span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold font-serif text-emerald-700">
              {summary ? `${summary.retention_policy_days} Days` : "..."}
            </span>
            <span className="text-xs text-slate-500">auto-purge limit</span>
          </div>
          <div className="mt-2 text-xs text-slate-600 flex justify-between">
            <span>Purged to Date:</span>
            <span className="font-semibold text-emerald-700">
              {summary ? summary.purged_frames : 0} frames
            </span>
          </div>
        </div>

        {/* Cryptographic Ledger Health */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Receipt Signing
            </span>
            <KeyRound className="w-4 h-4 text-institutional-navy" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-lg font-bold font-serif text-institutional-navy">
              HMAC-SHA256
            </span>
          </div>
          <div className="mt-2 text-xs text-slate-600 flex items-center space-x-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 inline" />
            <span>Tamper verification enabled</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Data Purging + Receipt Verification */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Section 1: Ephemeral Frame Purge Controller */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-4">
          <div className="flex items-center space-x-2">
            <Trash2 className="w-5 h-5 text-red-600" />
            <h2 className="font-serif font-bold text-lg text-slate-900">
              Ephemeral Raw Image Purge
            </h2>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Per institutional compliance directives, raw classroom capture images are ephemeral. Once attendance is finalized and verified, frames older than the retention threshold must be unlinked from physical storage. Finalized attendance ledgers and audit records remain intact.
          </p>

          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-900 flex items-start space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
            <span>
              Unlinking raw frames from disk is permanent and irreversible. All purge operations emit an immutable <strong className="font-mono">DATA_PURGE_EXECUTED</strong> audit event.
            </span>
          </div>

          <div className="space-y-3 pt-2">
            <label className="block text-xs font-medium text-slate-700">
              Retention Cutoff Window (Days post-finalization)
            </label>
            <div className="flex items-center space-x-3">
              <input
                type="number"
                min={0}
                max={365}
                value={retentionDays}
                onChange={(e) => setRetentionDays(Number(e.target.value))}
                className="w-28 px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-institutional-blue"
              />
              <span className="text-xs text-slate-500">
                Purges frames for sessions finalized &ge; {retentionDays} days ago
              </span>
            </div>

            <button
              type="button"
              onClick={handleExecutePurge}
              disabled={actionLoading === "purge"}
              className="w-full mt-2 flex items-center justify-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4" />
              <span>
                {actionLoading === "purge" ? "Unlinking Frames..." : `Execute Retention Purge (≥ ${retentionDays} Days)`}
              </span>
            </button>
          </div>

          {/* Purge Result Banner */}
          {purgeResult && (
            <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 space-y-1">
              <div className="font-semibold flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Purge Executed Successfully</span>
              </div>
              <div>Frames Unlinked: {purgeResult.purged_frames_count}</div>
              <div>Physical Storage Freed: {(purgeResult.freed_bytes / 1024).toFixed(1)} KB</div>
              <div className="font-mono text-slate-600 text-[11px]">Audit ID: {purgeResult.audit_event_id}</div>
            </div>
          )}

          {purgeError && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-800">
              Purge Error: {purgeError}
            </div>
          )}
        </div>

        {/* Section 2: Cryptographic Receipt Verifier */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-4">
          <div className="flex items-center space-x-2">
            <FileCheck2 className="w-5 h-5 text-institutional-navy" />
            <h2 className="font-serif font-bold text-lg text-slate-900">
              Cryptographic Receipt & Ledger Verifier
            </h2>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Verify the mathematical authenticity of committed session receipts. The verifier recomputes the HMAC-SHA256 signature using the server master secret and recalculates the attendance ledger hash across all student unit records to detect data tampering.
          </p>

          <form onSubmit={handleVerifyReceipt} className="space-y-3 pt-2">
            <label className="block text-xs font-medium text-slate-700">
              Session Identifier
            </label>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={verifySessionId}
                onChange={(e) => setVerifySessionId(e.target.value)}
                placeholder="e.g. SES-2026-CSE-401"
                className="flex-1 px-3 py-1.5 text-sm font-mono border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-institutional-blue"
              />
              <button
                type="submit"
                disabled={receiptLoading}
                className="px-4 py-1.5 bg-institutional-navy hover:bg-institutional-navy/90 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50"
              >
                {receiptLoading ? "Verifying..." : "Verify"}
              </button>
            </div>
          </form>

          {/* Verification Result Card */}
          {receiptResult && (
            <div className={`mt-3 p-3 rounded-lg border text-xs space-y-2 ${
              receiptResult.is_valid
                ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                : "bg-red-50 border-red-200 text-red-900"
            }`}>
              <div className="flex items-center justify-between font-bold">
                <span className="flex items-center space-x-1.5">
                  {receiptResult.is_valid ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-red-600" />
                  )}
                  <span>
                    {receiptResult.is_valid
                      ? "Cryptographic Verification Passed"
                      : "Verification Failed / Tamper Detected"}
                  </span>
                </span>
                <span className="font-mono text-[11px] px-2 py-0.5 rounded-full bg-white/60">
                  {receiptResult.is_valid ? "AUTHENTIC" : "INVALID"}
                </span>
              </div>
              <div className="space-y-1 font-mono text-[11px] text-slate-700">
                <div>HMAC Signature: {receiptResult.signature_valid ? "VALID" : "MISMATCH"}</div>
                <div>Ledger Hash Integrity: {receiptResult.ledger_integrity_valid ? "VALID" : "CORRUPTED"}</div>
                <div className="truncate">Stored Sig: {receiptResult.stored_signature}</div>
                <div className="truncate">Ledger Hash: {receiptResult.computed_ledger_hash}</div>
              </div>
              <p className="text-[11px] italic text-slate-600">{receiptResult.detail}</p>
            </div>
          )}

          {receiptError && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-800">
              Verification Query Error: {receiptError}
            </div>
          )}
        </div>
      </div>

      {/* Section 3: Student Biometric Consent & Non-Biometric Alternative Register */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-institutional-blue" />
            <div>
              <h2 className="font-serif font-bold text-lg text-slate-900">
                Student Biometric Consent & Non-Biometric Alternative Register
              </h2>
              <p className="text-xs text-slate-600">
                Under the institutional data privacy framework, biometric enrollment is consensual. Students with withheld consent must never be falsely marked absent; their attendance records are routed to manual faculty roll-call.
              </p>
            </div>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            {students.length} Registered Students
          </span>
        </div>

        {/* Table */}
        <div className="overflow-x-auto border border-slate-200 rounded-lg">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
              <tr>
                <th className="px-4 py-3 font-semibold">Roll Number</th>
                <th className="px-4 py-3 font-semibold">Full Name</th>
                <th className="px-4 py-3 font-semibold">Consent Status</th>
                <th className="px-4 py-3 font-semibold">Attendance Routing Policy</th>
                <th className="px-4 py-3 font-semibold text-right">Administrative Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {students.map((student) => {
                const isToggling = actionLoading === student.studentId;
                return (
                  <tr key={student.studentId} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-4 py-3 font-mono font-bold text-slate-900">
                      {student.rollNumber}
                    </td>
                    <td className="px-4 py-3 text-slate-800 font-medium">
                      {student.fullName}
                    </td>
                    <td className="px-4 py-3">
                      {student.biometricConsentActive ? (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          <span>Consent Active</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                          <AlertTriangle className="w-3 h-3 text-amber-600" />
                          <span>Consent Withheld</span>
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      {student.biometricConsentActive ? (
                        <span className="text-slate-700">Standard Biometric Vision Inference</span>
                      ) : (
                        <span className="font-semibold text-amber-800">
                          Non-Biometric Alternative Roll-Call Enforced
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => handleToggleConsent(student.studentId, student.biometricConsentActive)}
                        disabled={isToggling}
                        className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors disabled:opacity-50 ${
                          student.biometricConsentActive
                            ? "bg-amber-50 text-amber-900 hover:bg-amber-100 border border-amber-200"
                            : "bg-emerald-50 text-emerald-900 hover:bg-emerald-100 border border-emerald-200"
                        }`}
                      >
                        {isToggling ? "Updating..." : student.biometricConsentActive ? "Withhold Consent" : "Reinstate Consent"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

