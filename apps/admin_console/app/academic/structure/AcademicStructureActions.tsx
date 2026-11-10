"use client";

import React, { useState } from "react";
import { Plus, X, Building2, Layers, Calendar } from "lucide-react";
import { createDepartment, createCohort, DepartmentItem } from "@/lib/api";

interface Props {
  departments: DepartmentItem[];
}

export default function AcademicStructureActions({ departments }: Props) {
  const [modalType, setModalType] = useState<"DEPT" | "COHORT" | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Department Form
  const [deptCode, setDeptCode] = useState("");
  const [deptName, setDeptName] = useState("");

  // Cohort Form
  const [cohortDeptId, setCohortDeptId] = useState(departments[0]?.id || "");
  const [cohortName, setCohortName] = useState("");
  const [admYear, setAdmYear] = useState(2024);
  const [gradYear, setGradYear] = useState(2028);

  const handleCreateDept = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createDepartment(deptCode, deptName);
      alert(`Department ${deptCode} created successfully.`);
      setModalType(null);
      window.location.reload();
    } catch (err: any) {
      alert("Creation failed: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCreateCohort = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createCohort(cohortDeptId, cohortName, admYear, gradYear);
      alert(`Cohort ${cohortName} registered successfully.`);
      setModalType(null);
      window.location.reload();
    } catch (err: any) {
      alert("Creation failed: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <button
        type="button"
        onClick={() => setModalType("DEPT")}
        className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 shadow-xs"
      >
        <Building2 className="w-3.5 h-3.5 text-institutional-blue" />
        <span>Add Department</span>
      </button>

      <button
        type="button"
        onClick={() => setModalType("COHORT")}
        className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-institutional-navy text-white hover:bg-institutional-navy/90 shadow-xs"
      >
        <Layers className="w-3.5 h-3.5" />
        <span>Add Cohort</span>
      </button>

      {/* Department Modal */}
      {modalType === "DEPT" && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-sm w-full shadow-xl border border-slate-200 overflow-hidden">
            <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
              <h3 className="font-semibold text-sm text-institutional-navy flex items-center space-x-2">
                <Building2 className="w-4 h-4 text-institutional-blue" />
                <span>Create Academic Department</span>
              </h3>
              <button onClick={() => setModalType(null)} className="text-slate-400 hover:text-slate-700">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateDept} className="p-5 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">Department Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. MECH, ECE, CIVIL"
                  value={deptCode}
                  onChange={(e) => setDeptCode(e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-institutional-navy font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">Department Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Mechanical Engineering"
                  value={deptName}
                  onChange={(e) => setDeptName(e.target.value)}
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
                  {submitting ? "Saving..." : "Create Department"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Cohort Modal */}
      {modalType === "COHORT" && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-sm w-full shadow-xl border border-slate-200 overflow-hidden">
            <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
              <h3 className="font-semibold text-sm text-institutional-navy flex items-center space-x-2">
                <Layers className="w-4 h-4 text-indigo-600" />
                <span>Register Student Cohort</span>
              </h3>
              <button onClick={() => setModalType(null)} className="text-slate-400 hover:text-slate-700">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateCohort} className="p-5 space-y-3.5">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">Department</label>
                <select
                  value={cohortDeptId}
                  onChange={(e) => setCohortDeptId(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-institutional-navy"
                >
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.code} — {d.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">Cohort Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CSE-2024-2028"
                  value={cohortName}
                  onChange={(e) => setCohortName(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-institutional-navy font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">Admission Year</label>
                  <input
                    type="number"
                    required
                    value={admYear}
                    onChange={(e) => setAdmYear(parseInt(e.target.value) || 2024)}
                    className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-institutional-navy"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-700 mb-1">Graduation Year</label>
                  <input
                    type="number"
                    required
                    value={gradYear}
                    onChange={(e) => setGradYear(parseInt(e.target.value) || 2028)}
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
                  {submitting ? "Saving..." : "Register Cohort"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
