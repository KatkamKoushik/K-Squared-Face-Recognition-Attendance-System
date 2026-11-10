"use client";

import React, { useState } from "react";
import { Plus, X, BookOpen, UserCheck } from "lucide-react";
import { createOffering, assignFaculty, SubjectOfferingItem } from "@/lib/api";

interface Props {
  offerings: SubjectOfferingItem[];
}

export default function CourseOfferingsActions({ offerings }: Props) {
  const [modalType, setModalType] = useState<"OFFERING" | "ASSIGN" | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Offering form
  const [subjectId, setSubjectId] = useState("");
  const [termId, setTermId] = useState("");
  const [cohortId, setCohortId] = useState("");
  const [section, setSection] = useState("A");

  // Assignment form
  const [assignFacultyId, setAssignFacultyId] = useState("");
  const [assignOfferingId, setAssignOfferingId] = useState(offerings[0]?.id || "");
  const [startDate, setStartDate] = useState(new Date().toISOString().split("T")[0]);
  const [endDate, setEndDate] = useState("2026-12-31");

  const handleCreateOffering = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createOffering(subjectId, termId, cohortId, section);
      alert("Course offering registered successfully.");
      setModalType(null);
      window.location.reload();
    } catch (err: any) {
      alert("Creation failed: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleAssignFaculty = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await assignFaculty(assignFacultyId, assignOfferingId, startDate, endDate);
      alert("Faculty teaching assignment recorded.");
      setModalType(null);
      window.location.reload();
    } catch (err: any) {
      alert("Assignment failed: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <button
        type="button"
        onClick={() => setModalType("ASSIGN")}
        className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 shadow-xs"
      >
        <UserCheck className="w-3.5 h-3.5 text-institutional-blue" />
        <span>Assign Faculty</span>
      </button>

      <button
        type="button"
        onClick={() => setModalType("OFFERING")}
        className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-institutional-navy text-white hover:bg-institutional-navy/90 shadow-xs"
      >
        <Plus className="w-3.5 h-3.5" />
        <span>New Offering</span>
      </button>

      {/* New Offering Modal */}
      {modalType === "OFFERING" && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-sm w-full shadow-xl border border-slate-200 overflow-hidden">
            <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
              <h3 className="font-semibold text-sm text-institutional-navy flex items-center space-x-2">
                <BookOpen className="w-4 h-4 text-institutional-blue" />
                <span>Create Subject Offering</span>
              </h3>
              <button onClick={() => setModalType(null)} className="text-slate-400 hover:text-slate-700">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateOffering} className="p-5 space-y-3.5">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">Subject ID</label>
                <input
                  type="text"
                  required
                  placeholder="UUID or Subject ID"
                  value={subjectId}
                  onChange={(e) => setSubjectId(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-institutional-navy font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">Term ID</label>
                <input
                  type="text"
                  required
                  placeholder="Term ID (e.g., Odd 2026)"
                  value={termId}
                  onChange={(e) => setTermId(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-institutional-navy font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">Primary Cohort ID</label>
                <input
                  type="text"
                  required
                  placeholder="Cohort ID (e.g. CSE-2023-2027)"
                  value={cohortId}
                  onChange={(e) => setCohortId(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-institutional-navy font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">Section</label>
                <input
                  type="text"
                  required
                  placeholder="Section (e.g., A, B, Joint)"
                  value={section}
                  onChange={(e) => setSection(e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-institutional-navy"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setModalType(null)}
                  className="px-3 py-1.5 text-xs font-semibold rounded-lg text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-institutional-navy text-white hover:bg-institutional-navy/90 disabled:opacity-50"
                >
                  {submitting ? "Saving..." : "Create Offering"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Assign Faculty Modal */}
      {modalType === "ASSIGN" && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-sm w-full shadow-xl border border-slate-200 overflow-hidden">
            <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
              <h3 className="font-semibold text-sm text-institutional-navy flex items-center space-x-2">
                <UserCheck className="w-4 h-4 text-institutional-blue" />
                <span>Assign Teaching Faculty</span>
              </h3>
              <button onClick={() => setModalType(null)} className="text-slate-400 hover:text-slate-700">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAssignFaculty} className="p-5 space-y-3.5">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">Subject Offering</label>
                <select
                  value={assignOfferingId}
                  onChange={(e) => setAssignOfferingId(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-institutional-navy"
                >
                  {offerings.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.subject_name || o.id} (Sec {o.section})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">Faculty Member ID</label>
                <input
                  type="text"
                  required
                  placeholder="Faculty ID / Employee Code"
                  value={assignFacultyId}
                  onChange={(e) => setAssignFacultyId(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-institutional-navy font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">Start Date</label>
                  <input
                    type="date"
                    required
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-institutional-navy"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">End Date</label>
                  <input
                    type="date"
                    required
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-institutional-navy"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setModalType(null)}
                  className="px-3 py-1.5 text-xs font-semibold rounded-lg text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-institutional-navy text-white hover:bg-institutional-navy/90 disabled:opacity-50"
                >
                  {submitting ? "Saving..." : "Record Assignment"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
