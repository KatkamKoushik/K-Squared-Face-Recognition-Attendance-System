"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  X,
  RefreshCw,
  Eye,
  AlertCircle,
  Calendar,
  Building,
  User,
  ArrowLeft,
  Camera,
  UserPlus,
} from "lucide-react";
import {
  getEnrollmentSubmissions,
  approveEnrollmentSubmission,
  rejectEnrollmentSubmission,
  requestRecaptureEnrollmentSubmission,
  getSubmissionPhotoUrl,
  EnrollmentSubmissionItem,
  getAuthToken,
} from "@/lib/api";

export default function AdminEnrollmentQueuePage() {
  const [submissions, setSubmissions] = useState<EnrollmentSubmissionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchTerm, setSearchTerm] = useState<string>("");

  // Review modal state
  const [selectedSub, setSelectedSub] = useState<EnrollmentSubmissionItem | null>(null);
  const [reviewReason, setReviewReason] = useState<string>("");
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const token = getAuthToken();

  useEffect(() => {
    loadSubmissions();
  }, [statusFilter]);

  const loadSubmissions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getEnrollmentSubmissions(
        statusFilter === "ALL" ? undefined : statusFilter,
        searchTerm ? searchTerm : undefined
      );
      if (data) {
        setSubmissions(data);
      } else {
        setSubmissions([]);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load enrollment submissions.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadSubmissions();
  };

  const handleOpenReview = (sub: EnrollmentSubmissionItem) => {
    setSelectedSub(sub);
    setReviewReason("");
    setActionError(null);
    setActionSuccess(null);
  };

  const handleApprove = async () => {
    if (!selectedSub) return;
    setActionLoading(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      const updated = await approveEnrollmentSubmission(selectedSub.id);
      setActionSuccess(`Enrollment approved. SFace 128-D template generated and registered in gallery for ${updated.roll_number}.`);
      setSelectedSub(updated);
      loadSubmissions();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Approval failed";
      setActionError(msg);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRecapture = async () => {
    if (!selectedSub) return;
    if (!reviewReason.trim()) {
      setActionError("Please provide guidance notes explaining why recapture is required (e.g. lighting, angle, resolution).");
      return;
    }
    setActionLoading(true);
    setActionError(null);
    try {
      const updated = await requestRecaptureEnrollmentSubmission(selectedSub.id, reviewReason.trim());
      setActionSuccess(`Recapture requested for ${updated.roll_number}.`);
      setSelectedSub(updated);
      loadSubmissions();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Recapture request failed";
      setActionError(msg);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedSub) return;
    if (!reviewReason.trim()) {
      setActionError("Please provide an institutional reason for rejecting this enrollment application.");
      return;
    }
    setActionLoading(true);
    setActionError(null);
    try {
      const updated = await rejectEnrollmentSubmission(selectedSub.id, reviewReason.trim());
      setActionSuccess(`Enrollment application rejected for ${updated.roll_number}.`);
      setSelectedSub(updated);
      loadSubmissions();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Rejection failed";
      setActionError(msg);
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800">APPROVED</span>;
      case "REJECTED":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-red-100 text-red-800">REJECTED</span>;
      case "RECAPTURE_REQUIRED":
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-800">RECAPTURE REQUIRED</span>;
      case "PENDING_REVIEW":
      default:
        return <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800">PENDING REVIEW</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs text-slate-500 mb-1">
            <Link href="/admin" className="hover:text-institutional-navy flex items-center space-x-1">
              <ArrowLeft className="w-3 h-3" />
              <span>Executive Overview</span>
            </Link>
            <span>/</span>
            <span>Biometric Queue</span>
          </div>
          <h1 className="font-serif text-2xl font-bold text-institutional-navy">
            Student Biometric Enrollment Review Queue
          </h1>
          <p className="text-sm text-slate-500">
            Verify student identity details, inspect submitted frontal portraits, and approve face recognition templates.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            href="/enroll"
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-institutional-navy text-white hover:bg-institutional-navy/90 transition-colors shadow-xs"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Enroll Student (Web)</span>
          </Link>
          <button
            type="button"
            onClick={loadSubmissions}
            disabled={loading}
            className="inline-flex items-center space-x-2 px-3 py-2 border border-slate-300 rounded-lg text-xs font-semibold bg-white text-slate-700 hover:bg-slate-50 transition-colors shadow-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh Queue</span>
          </button>
        </div>
      </div>

      {/* Filter Tabs & Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          {/* Status Tabs */}
          <div className="flex flex-wrap gap-2">
            {[
              { label: "Pending Review", value: "PENDING_REVIEW" },
              { label: "Approved", value: "APPROVED" },
              { label: "Recapture Required", value: "RECAPTURE_REQUIRED" },
              { label: "Rejected", value: "REJECTED" },
              { label: "All Submissions", value: "ALL" },
            ].map((tab) => (
              <button
                key={tab.value}
                type="button"
                onClick={() => setStatusFilter(tab.value)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  statusFilter === tab.value
                    ? "bg-institutional-navy text-white shadow-xs"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search Form */}
          <form onSubmit={handleSearch} className="flex items-center space-x-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search roll number, name..."
                className="pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:outline-hidden focus:ring-1 focus:ring-institutional-navy focus:bg-white w-52 sm:w-64"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
            >
              Search
            </button>
          </form>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Submissions Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500 text-sm">
            <RefreshCw className="w-5 h-5 animate-spin mx-auto text-institutional-navy mb-2" />
            <span>Loading enrollment queue...</span>
          </div>
        ) : submissions.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <ShieldAlert className="w-8 h-8 mx-auto text-slate-400 mb-2" />
            <div className="text-sm font-semibold text-slate-700">No enrollment submissions found</div>
            <div className="text-xs text-slate-500 mt-1">
              There are no staged biometric submissions matching the selected filter ({statusFilter}).
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">Portrait</th>
                  <th className="py-3 px-4">Roll Number</th>
                  <th className="py-3 px-4">Student Name</th>
                  <th className="py-3 px-4">Department</th>
                  <th className="py-3 px-4">Academic Year</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Submission Date</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {submissions.map((sub) => (
                  <tr key={sub.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4">
                      <div
                        onClick={() => handleOpenReview(sub)}
                        className="cursor-pointer relative w-11 h-11 rounded-xl overflow-hidden border border-slate-200 bg-slate-100 flex items-center justify-center shrink-0 hover:ring-2 hover:ring-institutional-navy transition-all shadow-xs"
                        title="Click to inspect portrait"
                      >
                        {sub.photo_storage_path ? (
                          <img
                            src={getSubmissionPhotoUrl(sub.id, sub.photo_storage_path)}
                            alt={sub.full_name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <Camera className="w-5 h-5 text-slate-400" />
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-slate-900">{sub.roll_number}</td>
                    <td className="py-3 px-4 font-medium text-slate-800">{sub.full_name}</td>
                    <td className="py-3 px-4 text-slate-600">{sub.department}</td>
                    <td className="py-3 px-4 text-slate-600">{sub.academic_year}</td>
                    <td className="py-3 px-4">{getStatusBadge(sub.status)}</td>
                    <td className="py-3 px-4 text-slate-500">
                      {new Date(sub.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        type="button"
                        onClick={() => handleOpenReview(sub)}
                        className="inline-flex items-center space-x-1.5 px-3 py-1 bg-institutional-navy/10 hover:bg-institutional-navy text-institutional-navy hover:text-white rounded-lg font-semibold transition-colors text-[11px]"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect & Review</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Review & Adjudication Modal */}
      {selectedSub && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-2xl w-full p-6 space-y-6 my-8">
            <div className="flex items-center justify-between border-b border-slate-200 pb-4">
              <div>
                <h2 className="text-lg font-serif font-bold text-institutional-navy">
                  Biometric Portrait Inspection & Verification
                </h2>
                <div className="text-xs text-slate-500">
                  Application ID: <span className="font-mono">{selectedSub.id}</span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedSub(null)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-md transition-colors"
                title="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {actionError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                <span>{actionError}</span>
              </div>
            )}

            {actionSuccess && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-700 flex items-start space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span>{actionSuccess}</span>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Photo Display */}
              <div className="space-y-2 text-center">
                <div className="w-48 h-60 mx-auto rounded-xl overflow-hidden border-2 border-slate-300 shadow-md bg-slate-100 flex items-center justify-center relative">
                  <img
                    src={getSubmissionPhotoUrl(selectedSub.id, selectedSub.photo_storage_path)}
                    alt={`${selectedSub.roll_number} Portrait`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.currentTarget as HTMLImageElement).src = "";
                      (e.currentTarget as HTMLImageElement).alt = "Photo requires authenticated admin session";
                    }}
                  />
                </div>
                <div className="text-[11px] text-slate-500 font-mono">
                  SHA-256: {selectedSub.photo_sha256.substring(0, 16)}...
                </div>
              </div>

              {/* Student Metadata */}
              <div className="space-y-3 text-xs">
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Roll Number:</span>
                    <span className="font-mono font-bold text-slate-900">{selectedSub.roll_number}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Full Name:</span>
                    <span className="font-semibold text-slate-900">{selectedSub.full_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Email:</span>
                    <span className="text-slate-800">{selectedSub.institutional_email}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Department:</span>
                    <span className="font-medium text-slate-800">{selectedSub.department}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Academic Year:</span>
                    <span className="text-slate-800">{selectedSub.academic_year}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Current Status:</span>
                    <span>{getStatusBadge(selectedSub.status)}</span>
                  </div>
                </div>

                {selectedSub.rejection_reason && (
                  <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-[11px] text-amber-900">
                    <strong>Previous Note:</strong> {selectedSub.rejection_reason}
                  </div>
                )}

                {/* Reason Notes for Recapture or Rejection */}
                <div>
                  <label htmlFor="adjudicationReason" className="block text-[11px] font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Guidance / Rejection Notes (Required for Recapture/Reject)
                  </label>
                  <textarea
                    id="adjudicationReason"
                    rows={3}
                    value={reviewReason}
                    onChange={(e) => setReviewReason(e.target.value)}
                    placeholder="e.g. Portrait too dark, face partially occluded, or please look straight at camera..."
                    className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs focus:outline-hidden focus:ring-1 focus:ring-institutional-navy"
                  />
                </div>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="pt-4 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => setSelectedSub(null)}
                className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50"
              >
                Close
              </button>

              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={handleReject}
                  className="px-3.5 py-2 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 rounded-lg text-xs font-semibold disabled:opacity-50 transition-colors"
                >
                  Reject Application
                </button>
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={handleRecapture}
                  className="px-3.5 py-2 bg-blue-50 hover:bg-blue-100 text-institutional-blue border border-blue-200 rounded-lg text-xs font-semibold disabled:opacity-50 transition-colors"
                >
                  Request Recapture
                </button>
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={handleApprove}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold disabled:opacity-50 transition-colors shadow-xs flex items-center space-x-1.5"
                >
                  {actionLoading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Generating Template...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Approve & Generate SFace Template</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
