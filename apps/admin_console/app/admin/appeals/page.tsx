"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldCheck,
  Search,
  Filter,
  Check,
  X,
  MessageSquare,
} from "lucide-react";
import { getAllAppeals, reviewAppeal, AttendanceAppealItem } from "@/lib/api";

export default function AdminAppealsPage() {
  const [appeals, setAppeals] = useState<AttendanceAppealItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<"ALL" | "PENDING" | "APPROVED" | "REJECTED">("PENDING");
  const [search, setSearch] = useState("");

  // Review Modal State
  const [activeAppeal, setActiveAppeal] = useState<AttendanceAppealItem | null>(null);
  const [decision, setDecision] = useState<"APPROVE" | "REJECT">("APPROVE");
  const [reviewNotes, setReviewNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadAppeals();
  }, []);

  const loadAppeals = async () => {
    setLoading(true);
    try {
      const data = await getAllAppeals();
      setAppeals(data || []);
    } catch (err: any) {
      alert("Failed to load appeals: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenReview = (appeal: AttendanceAppealItem, action: "APPROVE" | "REJECT") => {
    setActiveAppeal(appeal);
    setDecision(action);
    setReviewNotes(action === "APPROVE" ? "Official duty certificate verified." : "Insufficient documentation provided.");
  };

  const handleConfirmDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeAppeal) return;
    setSubmitting(true);
    try {
      await reviewAppeal(activeAppeal.id, decision === "APPROVE", reviewNotes);
      setActiveAppeal(null);
      await loadAppeals();
    } catch (err: any) {
      alert("Review action failed: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredAppeals = appeals.filter((a) => {
    if (filterStatus !== "ALL" && a.status !== filterStatus) return false;
    if (search) {
      const query = search.toLowerCase();
      return (
        a.reason.toLowerCase().includes(query) ||
        a.id.toLowerCase().includes(query) ||
        a.session_id.toLowerCase().includes(query)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl font-bold text-institutional-navy">
            Student Attendance Appeals Queue
          </h1>
          <p className="text-sm text-institutional-muted">
            Official institutional review and audited ledger corrections for disputed classroom attendance.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={loadAppeals}
            className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 shadow-xs"
          >
            Refresh Queue
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by reason or ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:ring-2 focus:ring-institutional-navy"
            />
          </div>
        </div>

        <div className="flex items-center space-x-1.5 self-end sm:self-auto">
          {(["PENDING", "ALL", "APPROVED", "REJECTED"] as const).map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                filterStatus === st
                  ? "bg-institutional-navy text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {st === "ALL" ? "All Appeals" : st}
            </button>
          ))}
        </div>
      </div>

      {/* Appeals Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-600 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">Appeal ID</th>
                <th className="px-6 py-3">Student & Session Details</th>
                <th className="px-6 py-3">Justification Reason</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-xs text-slate-500">
                    Loading appeals from database...
                  </td>
                </tr>
              ) : filteredAppeals.length > 0 ? (
                filteredAppeals.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs text-slate-500">
                      {app.id.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-4 text-xs">
                      <span className="font-mono text-slate-700 block">Student: {app.student_id.substring(0, 8)}...</span>
                      <span className="text-slate-500 block">Session: {app.session_id.substring(0, 8)}...</span>
                      <span className="text-slate-400 block font-mono text-[11px]">Unit: {app.unit_id.substring(0, 8)}...</span>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-800 max-w-sm">
                      <p className="leading-relaxed">{app.reason}</p>
                      {app.review_notes && (
                        <p className="mt-1 text-slate-500 italic text-[11px]">
                          Note: "{app.review_notes}"
                        </p>
                      )}
                    </td>
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
                    </td>
                    <td className="px-6 py-4 text-right">
                      {app.status === "PENDING" ? (
                        <div className="inline-flex items-center space-x-1.5">
                          <button
                            onClick={() => handleOpenReview(app, "APPROVE")}
                            className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 transition-colors"
                          >
                            <Check className="w-3.5 h-3.5" />
                            <span>Approve</span>
                          </button>
                          <button
                            onClick={() => handleOpenReview(app, "REJECT")}
                            className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-rose-600 text-white text-xs font-semibold hover:bg-rose-700 transition-colors"
                          >
                            <X className="w-3.5 h-3.5" />
                            <span>Reject</span>
                          </button>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400">Decided</span>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-xs text-slate-500">
                    No appeals found matching criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Decision Modal */}
      {activeAppeal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
              <h3 className="font-semibold text-sm text-institutional-navy">
                {decision === "APPROVE" ? "Approve Attendance Appeal" : "Reject Attendance Appeal"}
              </h3>
              <button onClick={() => setActiveAppeal(null)} className="text-slate-400 hover:text-slate-700">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleConfirmDecision} className="p-6 space-y-4">
              <div className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg space-y-1">
                <div>
                  <span className="font-semibold">Appeal ID:</span> {activeAppeal.id}
                </div>
                <div>
                  <span className="font-semibold">Reason:</span> {activeAppeal.reason}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">
                  Official Administrative Review Notes
                </label>
                <textarea
                  required
                  rows={3}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="State the institutional reason for approval or rejection..."
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-institutional-navy"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setActiveAppeal(null)}
                  className="px-3.5 py-2 text-xs font-semibold rounded-lg text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className={`px-4 py-2 text-xs font-semibold rounded-lg text-white transition-colors flex items-center space-x-1.5 ${
                    decision === "APPROVE"
                      ? "bg-emerald-600 hover:bg-emerald-700"
                      : "bg-rose-600 hover:bg-rose-700"
                  }`}
                >
                  <span>{submitting ? "Processing..." : `Confirm ${decision === "APPROVE" ? "Approval" : "Rejection"}`}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
