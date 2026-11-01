import React from "react";
import { GitMerge, Users, ShieldAlert, Database, Plus, CheckCircle2 } from "lucide-react";
import { getAuthorizedGroups, AuthorizedClassGroupItem } from "@/lib/api";

const mockGroups: (AuthorizedClassGroupItem & { student_count?: number; offering_code?: string; description?: string })[] = [
  {
    id: "grp-cs302-joint",
    offering_id: "off-cs302-2026-a",
    offering_code: "CS302 Database Engineering",
    group_name: "CSE-III Joint Theory (Section A + Section B)",
    description: "Merged theory lecture session combining Section A (42 students) and Section B (44 students)",
    student_count: 86,
    is_active: true,
    member_cohort_ids: ["coh-cse-2023-secA", "coh-cse-2023-secB"],
  },
  {
    id: "grp-open-elective-01",
    offering_id: "off-cs405-2026",
    offering_code: "CS405 Cloud Architecture & DevOps",
    group_name: "Institute Open Elective (CSE + ECE Final Year)",
    description: "Cross-departmental open elective lecture held in Central Auditorium (LH-101)",
    student_count: 112,
    is_active: true,
    member_cohort_ids: ["coh-cse-2022", "coh-ece-2022"],
  },
  {
    id: "grp-honors-ai-01",
    offering_id: "off-ai701-2026",
    offering_code: "AI701 Advanced Deep Learning Honors",
    group_name: "B.Tech Honors Combined Specialization Group",
    description: "Honors track batch meeting for advanced research seminar",
    student_count: 28,
    is_active: false,
    member_cohort_ids: ["coh-cse-2022-honors", "coh-ds-2022-honors"],
  },
];

export default async function JointClassGroupsPage() {
  const serverGroups = await getAuthorizedGroups();
  const isLive = serverGroups !== null && serverGroups.length > 0;
  const groups = isLive ? serverGroups : mockGroups;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-bold text-institutional-navy">
            Authorized Joint-Class Groups & Section Unions
          </h1>
          <p className="text-sm text-institutional-muted">
            Manage multi-cohort merged class groups, section unions for shared electives, and combined attendance boundaries.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-full border bg-white shadow-xs">
            <Database className={`w-3.5 h-3.5 ${isLive ? "text-emerald-600" : "text-slate-400"}`} />
            <span className={isLive ? "text-emerald-700 font-mono" : "text-slate-600"}>
              {isLive ? "LIVE GROUPS REGISTRY" : "JOINT GROUPS BASELINE"}
            </span>
          </div>
          <button
            type="button"
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium bg-institutional-navy text-white hover:bg-institutional-navy/90 transition-colors shadow-xs"
          >
            <Plus className="w-4 h-4" />
            <span>Create Joint Group</span>
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-institutional-muted">
              Total Joint Groups
            </span>
            <GitMerge className="w-5 h-5 text-institutional-blue" />
          </div>
          <div className="mt-2 text-2xl font-serif font-bold text-institutional-navy">
            {groups.length}
          </div>
          <p className="mt-1 text-xs text-slate-500">Configured institutional combinations</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-institutional-muted">
              Active Attendance Unions
            </span>
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-serif font-bold text-institutional-navy">
            {groups.filter((g) => g.is_active).length} Active
          </div>
          <p className="mt-1 text-xs text-slate-500">Eligible for session scheduling</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-institutional-muted">
              Combined Enrolment Reach
            </span>
            <Users className="w-5 h-5 text-indigo-600" />
          </div>
          <div className="mt-2 text-2xl font-serif font-bold text-institutional-navy">
            226 Students
          </div>
          <p className="mt-1 text-xs text-slate-500">Across multi-cohort lecture sections</p>
        </div>
      </div>

      {/* Joint Groups Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <h2 className="text-base font-semibold text-institutional-navy flex items-center space-x-2">
            <GitMerge className="w-4 h-4 text-institutional-blue" />
            <span>Authorized Joint Groups</span>
          </h2>
          <span className="text-xs text-slate-500">Deduplicated Attendance Boundaries</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-600 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">Group Name & ID</th>
                <th className="px-6 py-3">Course Offering Reference</th>
                <th className="px-6 py-3">Member Cohort Constituents</th>
                <th className="px-6 py-3 text-center">Enrolled Students</th>
                <th className="px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {groups.map((grp) => {
                const grpWithMeta = grp as AuthorizedClassGroupItem & { student_count?: number; offering_code?: string; description?: string };
                return (
                  <tr key={grp.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-800">{grp.group_name}</div>
                      <div className="text-xs font-mono text-institutional-blue mt-0.5">{grp.id}</div>
                      {grpWithMeta.description && (
                        <div className="text-xs text-slate-500 mt-1 max-w-md">{grpWithMeta.description}</div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-800">
                        {grpWithMeta.offering_code || grp.offering_id}
                      </div>
                      <div className="text-xs font-mono text-slate-500 mt-0.5">
                        Offering Ref: {grp.offering_id}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1.5">
                        {grp.member_cohort_ids.map((cohortId) => (
                          <span
                            key={cohortId}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono bg-slate-100 text-slate-700 border border-slate-200"
                          >
                            {cohortId}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className="font-mono font-semibold text-slate-800">
                        {grpWithMeta.student_count || "—"}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${grp.is_active ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-slate-100 text-slate-600 border-slate-300"}`}>
                        {grp.is_active ? "Active" : "Disabled"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section Union Deduplication Rule Invariant */}
      <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex items-start space-x-3 text-xs text-slate-600">
        <ShieldAlert className="w-4 h-4 text-institutional-navy flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-800">Section Union Invariant:</span> When a session is initiated with an authorized joint-class group, the roster freeze captures the unique union of all active students in the member cohorts. Student duplicates across sections are eliminated by primary roll number, guaranteeing single-denominator fairness.
        </div>
      </div>
    </div>
  );
}

