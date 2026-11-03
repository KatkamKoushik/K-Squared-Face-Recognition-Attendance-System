import React from "react";
import { Building2, Calendar, Layers, ShieldCheck, Database, Plus } from "lucide-react";
import { getDepartments, getCohorts, getTerms, DepartmentItem, CohortItem, TermItem } from "@/lib/api";

const mockDepartments: DepartmentItem[] = [
  { id: "dept-cse-01", code: "CSE", name: "Computer Science & Engineering", created_at: "2009-08-01T09:00:00Z" },
  { id: "dept-ece-01", code: "ECE", name: "Electronics & Communication Engineering", created_at: "2009-08-01T09:00:00Z" },
  { id: "dept-eee-01", code: "EEE", name: "Electrical & Electronics Engineering", created_at: "2009-08-01T09:00:00Z" },
  { id: "dept-me-01", code: "MECH", name: "Mechanical Engineering", created_at: "2009-08-01T09:00:00Z" },
  { id: "dept-ce-01", code: "CIVIL", name: "Civil Engineering", created_at: "2009-08-01T09:00:00Z" },
  { id: "dept-it-01", code: "IT", name: "Information Technology", created_at: "2010-08-01T09:00:00Z" },
  { id: "dept-csd-01", code: "CSD", name: "Computer Science & Engineering (Data Science)", created_at: "2021-08-01T09:00:00Z" },
];

const mockCohorts: CohortItem[] = [
  { id: "coh-cse-2022", department_id: "dept-cse-01", name: "B.Tech CSE Class of 2026 (Final Year IV/IV)", admission_year: 2022, graduation_year: 2026, is_active: true },
  { id: "coh-cse-2023", department_id: "dept-cse-01", name: "B.Tech CSE Class of 2027 (Third Year III/IV)", admission_year: 2023, graduation_year: 2027, is_active: true },
  { id: "coh-it-2022", department_id: "dept-it-01", name: "B.Tech IT Class of 2026 (Final Year IV/IV)", admission_year: 2022, graduation_year: 2026, is_active: true },
  { id: "coh-csd-2023", department_id: "dept-csd-01", name: "B.Tech CSD Class of 2027 (Third Year III/IV)", admission_year: 2023, graduation_year: 2027, is_active: true },
  { id: "coh-ece-2022", department_id: "dept-ece-01", name: "B.Tech ECE Class of 2026 (Final Year IV/IV)", admission_year: 2022, graduation_year: 2026, is_active: true },
  { id: "coh-eee-2022", department_id: "dept-eee-01", name: "B.Tech EEE Class of 2026 (Final Year IV/IV)", admission_year: 2022, graduation_year: 2026, is_active: true },
  { id: "coh-me-2022", department_id: "dept-me-01", name: "B.Tech MECH Class of 2026 (Final Year IV/IV)", admission_year: 2022, graduation_year: 2026, is_active: true },
  { id: "coh-ce-2022", department_id: "dept-ce-01", name: "B.Tech CIVIL Class of 2026 (Final Year IV/IV)", admission_year: 2022, graduation_year: 2026, is_active: true },
];

const mockTerms: TermItem[] = [
  { id: "term-2026-odd", academic_year_id: "ay-2026-2027", name: "KUCET Academic Year 2026-27 - Semester VII (Odd)", start_date: "2026-08-01", end_date: "2026-12-15", is_active: true },
  { id: "term-2026-even", academic_year_id: "ay-2026-2027", name: "KUCET Academic Year 2026-27 - Semester VIII (Even)", start_date: "2027-01-05", end_date: "2027-05-20", is_active: false },
  { id: "term-2025-even", academic_year_id: "ay-2025-2026", name: "KUCET Academic Year 2025-26 - Semester VI (Even)", start_date: "2026-01-05", end_date: "2026-05-20", is_active: false },
];

export default async function AcademicStructurePage() {
  const [serverDepts, serverCohorts, serverTerms] = await Promise.all([
    getDepartments(),
    getCohorts(),
    getTerms(),
  ]);

  const isLive = serverDepts !== null && serverDepts.length > 0;
  const departments = isLive ? serverDepts : mockDepartments;
  const cohorts = (serverCohorts && serverCohorts.length > 0) ? serverCohorts : mockCohorts;
  const terms = (serverTerms && serverTerms.length > 0) ? serverTerms : mockTerms;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-bold text-institutional-navy">
            Academic Structure & Institutional Hierarchy
          </h1>
          <p className="text-sm text-institutional-muted">
            Configure departments, graduation cohorts, academic calendars, and active operational terms.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-full border bg-white shadow-xs">
            <Database className={`w-3.5 h-3.5 ${isLive ? "text-emerald-600" : "text-slate-400"}`} />
            <span className={isLive ? "text-emerald-700 font-mono" : "text-slate-600"}>
              {isLive ? "LIVE CONTROL PLANE" : "STRUCTURAL BASELINE"}
            </span>
          </div>
          <button
            type="button"
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium bg-institutional-navy text-white hover:bg-institutional-navy/90 transition-colors shadow-xs"
          >
            <Plus className="w-4 h-4" />
            <span>Add Cohort</span>
          </button>
        </div>
      </div>

      {/* Structural Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-institutional-muted">
              Active Departments
            </span>
            <Building2 className="w-5 h-5 text-institutional-blue" />
          </div>
          <div className="mt-2 text-2xl font-serif font-bold text-institutional-navy">
            {departments.length}
          </div>
          <p className="mt-1 text-xs text-slate-500">Autonomous engineering faculties</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-institutional-muted">
              Registered Cohorts
            </span>
            <Layers className="w-5 h-5 text-indigo-600" />
          </div>
          <div className="mt-2 text-2xl font-serif font-bold text-institutional-navy">
            {cohorts.length}
          </div>
          <p className="mt-1 text-xs text-slate-500">Graduation classes (2022 – 2027)</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-institutional-muted">
              Academic Terms
            </span>
            <Calendar className="w-5 h-5 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-serif font-bold text-institutional-navy">
            {terms.filter((t) => t.is_active).length} Active / {terms.length} Total
          </div>
          <p className="mt-1 text-xs text-slate-500">Current calendar semester lock</p>
        </div>
      </div>

      {/* Departments Section */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <h2 className="text-base font-semibold text-institutional-navy flex items-center space-x-2">
            <Building2 className="w-4 h-4 text-institutional-blue" />
            <span>Academic Departments</span>
          </h2>
          <span className="text-xs text-slate-500">Authoritative Institutional Division</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-600 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3">Code</th>
                <th className="px-6 py-3">Department Name</th>
                <th className="px-6 py-3">Identifier</th>
                <th className="px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {departments.map((dept) => (
                <tr key={dept.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="px-6 py-4 font-mono font-bold text-institutional-blue">{dept.code}</td>
                  <td className="px-6 py-4 font-medium text-slate-800">{dept.name}</td>
                  <td className="px-6 py-4 font-mono text-xs text-slate-500">{dept.id}</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Active
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cohorts & Terms Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cohorts */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
            <h2 className="text-base font-semibold text-institutional-navy flex items-center space-x-2">
              <Layers className="w-4 h-4 text-indigo-600" />
              <span>Student Cohorts</span>
            </h2>
            <span className="text-xs text-slate-500">Enrolment Units</span>
          </div>
          <div className="divide-y divide-slate-100">
            {cohorts.map((cohort) => (
              <div key={cohort.id} className="p-4 flex items-center justify-between hover:bg-slate-50/50">
                <div>
                  <div className="font-semibold text-slate-800 text-sm">{cohort.name}</div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    Admission: {cohort.admission_year} • Graduation: {cohort.graduation_year}
                  </div>
                </div>
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${cohort.is_active ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-slate-100 text-slate-600 border-slate-300"}`}>
                  {cohort.is_active ? "Active" : "Archived"}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Operational Terms */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
            <h2 className="text-base font-semibold text-institutional-navy flex items-center space-x-2">
              <Calendar className="w-4 h-4 text-emerald-600" />
              <span>Operational Terms</span>
            </h2>
            <span className="text-xs text-slate-500">Academic Calendar</span>
          </div>
          <div className="divide-y divide-slate-100">
            {terms.map((term) => (
              <div key={term.id} className="p-4 flex items-center justify-between hover:bg-slate-50/50">
                <div>
                  <div className="font-semibold text-slate-800 text-sm">{term.name}</div>
                  <div className="text-xs text-slate-500 mt-0.5 font-mono">
                    {term.start_date} to {term.end_date}
                  </div>
                </div>
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${term.is_active ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-slate-100 text-slate-600 border-slate-300"}`}>
                  {term.is_active ? "Current Active" : "Scheduled"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Invariant Footer Callout */}
      <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 flex items-start space-x-3 text-xs text-slate-600">
        <ShieldCheck className="w-4 h-4 text-institutional-blue flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-800">Academic Calendar Invariant:</span> Attendance session timestamps must strictly fall within the active operational term&apos;s verified start and end dates. Sessions outside active terms are rejected by the FastAPI Control Plane validation layer.
        </div>
      </div>
    </div>
  );
}

