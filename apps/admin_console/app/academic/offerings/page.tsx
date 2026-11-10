import React from "react";
import { BookOpen, UserCheck, Shield, Database, Plus, Clock } from "lucide-react";
import { getOfferings, getFacultyAssignments, SubjectOfferingItem, FacultyAssignmentItem } from "@/lib/api";

export default async function CourseOfferingsPage() {
  const [serverOfferings, serverAssignments] = await Promise.all([
    getOfferings(),
    getFacultyAssignments(),
  ]);

  const isLive = serverOfferings !== null;
  const offerings = serverOfferings ?? [];
  const assignments = serverAssignments ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-bold text-institutional-navy">
            Course Offerings & Faculty Teaching Assignments
          </h1>
          <p className="text-sm text-institutional-muted">
            Configure term-specific course offerings, planned unit defaults, and authorized teaching assignments.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-full border bg-white shadow-xs">
            <Database className={`w-3.5 h-3.5 ${isLive ? "text-emerald-600" : "text-slate-400"}`} />
            <span className={isLive ? "text-emerald-700 font-mono" : "text-slate-600"}>
              {isLive ? "LIVE OFFERINGS REGISTRY" : "OFFERINGS DATABASE"}
            </span>
          </div>
          <button
            type="button"
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium bg-institutional-navy text-white hover:bg-institutional-navy/90 transition-colors shadow-xs"
          >
            <Plus className="w-4 h-4" />
            <span>New Course Offering</span>
          </button>
        </div>
      </div>

      {/* Offerings Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <h2 className="text-base font-semibold text-institutional-navy flex items-center space-x-2">
            <BookOpen className="w-4 h-4 text-institutional-blue" />
            <span>Active Course Offerings</span>
          </h2>
          <span className="text-xs text-slate-500">Term Semester VII (Odd 2026)</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-600 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">Offering ID</th>
                <th className="px-6 py-3">Subject / Course</th>
                <th className="px-6 py-3">Section</th>
                <th className="px-6 py-3 text-center">Planned Units Default</th>
                <th className="px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {offerings.length > 0 ? (
                offerings.map((offering) => {
                  const offWithMeta = offering as SubjectOfferingItem & { subject_name?: string; subject_code?: string };
                  return (
                    <tr key={offering.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-6 py-4 font-mono text-xs font-semibold text-institutional-blue">
                        {offering.id}
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-semibold text-slate-800">
                          {offWithMeta.subject_code ? `${offWithMeta.subject_code} • ` : ""}{offWithMeta.subject_name || offering.subject_id}
                        </div>
                        <div className="text-xs text-slate-500 font-mono mt-0.5">
                          Subject Ref: {offering.subject_id} • Cohort Ref: {offering.cohort_id}
                        </div>
                      </td>
                      <td className="px-6 py-4 font-medium text-slate-700">
                        {offering.section || "Default"}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-slate-100 text-institutional-navy border border-slate-200">
                          <Clock className="w-3 h-3 mr-1 text-institutional-blue" />
                          {offering.planned_units_default} Units
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${offering.is_active ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-slate-100 text-slate-600 border-slate-300"}`}>
                          {offering.is_active ? "Active" : "Archived"}
                        </span>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                    No course offerings registered in the active database.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Teaching Assignments Section */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <h2 className="text-base font-semibold text-institutional-navy flex items-center space-x-2">
            <UserCheck className="w-4 h-4 text-institutional-blue" />
            <span>Authorized Faculty Teaching Assignments</span>
          </h2>
          <span className="text-xs text-slate-500">Instructor Authorization & Session Permissions</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-600 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">Faculty Member</th>
                <th className="px-6 py-3">Assigned Offering / Target</th>
                <th className="px-6 py-3">Teaching Role</th>
                <th className="px-6 py-3">Active Validity Window</th>
                <th className="px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {assignments.length > 0 ? (
                assignments.map((asg) => {
                  const asgWithMeta = asg as FacultyAssignmentItem & { faculty_name?: string; subject_label?: string };
                  return (
                    <tr key={asg.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-semibold text-slate-800">
                          {asgWithMeta.faculty_name || asg.faculty_id}
                        </div>
                        <div className="text-xs font-mono text-slate-500">
                          ID: {asg.faculty_id}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-800">
                          {asgWithMeta.subject_label || asg.offering_id}
                        </div>
                        {asg.class_group_id && (
                          <div className="text-xs font-mono text-indigo-600 mt-0.5">
                            Joint Group: {asg.class_group_id}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                          {asg.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-slate-600">
                        {asg.start_date} to {asg.end_date}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${asg.is_active ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-slate-100 text-slate-600 border-slate-300"}`}>
                          {asg.is_active ? "Active" : "Expired"}
                        </span>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                    No faculty teaching assignments registered in the active database.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Governance Security Invariant */}
      <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex items-start space-x-3 text-xs text-slate-600">
        <Shield className="w-4 h-4 text-institutional-navy flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-800">Faculty Authorization Invariant:</span> Only faculty members with an active, valid teaching assignment for a specific course offering can initialize or commit attendance sessions. Unassigned faculty sessions fail with <code className="font-mono bg-slate-200 px-1 py-0.5 rounded">HTTP 403 INSUFFICIENT_PERMISSIONS</code>.
        </div>
      </div>
    </div>
  );
}
