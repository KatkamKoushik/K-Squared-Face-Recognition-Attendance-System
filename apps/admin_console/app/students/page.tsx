import React from "react";
import { UserPlus, Search, Filter, ShieldAlert, Database } from "lucide-react";
import { getStudents } from "@/lib/api";

interface StudentDirectoryRow {
  studentId: string;
  rollNumber: string;
  fullName: string;
  department: string;
  cohort: string;
  enrollmentStatus: "ACTIVE" | "ON_LEAVE" | "GRADUATED";
  effectiveStartDate: string;
}

const mockStudents: StudentDirectoryRow[] = [
  {
    studentId: "STU-KUCET-00622501",
    rollNumber: "00622501",
    fullName: "Katkam Koushik",
    department: "Computer Science & Engineering",
    cohort: "B.Tech CSE - Final Year (IV/IV Sec A)",
    enrollmentStatus: "ACTIVE",
    effectiveStartDate: "2022-08-01",
  },
  {
    studentId: "STU-KUCET-00622502",
    rollNumber: "00622502",
    fullName: "A. Sai Teja",
    department: "Computer Science & Engineering",
    cohort: "B.Tech CSE - Final Year (IV/IV Sec A)",
    enrollmentStatus: "ACTIVE",
    effectiveStartDate: "2022-08-01",
  },
  {
    studentId: "STU-KUCET-00622503",
    rollNumber: "00622503",
    fullName: "B. Manasa Reddy",
    department: "Computer Science & Engineering",
    cohort: "B.Tech CSE - Final Year (IV/IV Sec A)",
    enrollmentStatus: "ACTIVE",
    effectiveStartDate: "2022-08-01",
  },
  {
    studentId: "STU-KUCET-00622504",
    rollNumber: "00622504",
    fullName: "Ch. Rahul",
    department: "Computer Science & Engineering",
    cohort: "B.Tech CSE - Final Year (IV/IV Sec A)",
    enrollmentStatus: "ACTIVE",
    effectiveStartDate: "2022-08-01",
  },
  {
    studentId: "STU-KUCET-00622505",
    rollNumber: "00622505",
    fullName: "D. Ananya",
    department: "Computer Science & Engineering",
    cohort: "B.Tech CSE - Final Year (IV/IV Sec A)",
    enrollmentStatus: "ACTIVE",
    effectiveStartDate: "2022-08-01",
  },
  {
    studentId: "STU-KUCET-00622506",
    rollNumber: "00622506",
    fullName: "E. Srikanth",
    department: "Computer Science & Engineering",
    cohort: "B.Tech CSE - Final Year (IV/IV Sec A)",
    enrollmentStatus: "ACTIVE",
    effectiveStartDate: "2022-08-01",
  },
  {
    studentId: "STU-KUCET-00622507",
    rollNumber: "00622507",
    fullName: "G. Akhil Kumar",
    department: "Computer Science & Engineering",
    cohort: "B.Tech CSE - Final Year (IV/IV Sec A)",
    enrollmentStatus: "ACTIVE",
    effectiveStartDate: "2022-08-01",
  },
];

export default async function StudentsDirectoryPage() {
  const serverStudents = await getStudents();
  const isLive = serverStudents !== null && serverStudents.length > 0;

  const students: StudentDirectoryRow[] = isLive
    ? serverStudents.map((s) => ({
        studentId: s.id,
        rollNumber: s.roll_number,
        fullName: s.full_name,
        department: "Computer Science & Engineering",
        cohort: `Term ${s.current_term}`,
        enrollmentStatus: (s.status as any) || "ACTIVE",
        effectiveStartDate: s.enrollment_date || "2023-08-01",
      }))
    : mockStudents;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-bold text-institutional-navy">
            Student Directory & Enrolment Management
          </h1>
          <p className="text-sm text-institutional-muted">
            Authoritative student registry, effective enrolment periods, and cohort assignments.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-full border bg-white shadow-xs">
            <Database className={`w-3.5 h-3.5 ${isLive ? "text-emerald-600" : "text-slate-400"}`} />
            <span className={isLive ? "text-emerald-700 font-mono" : "text-slate-600"}>
              {isLive ? "LIVE ACADEMIC REGISTRY" : "REGISTRY SNAPSHOT"}
            </span>
          </div>
          <button
            type="button"
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium bg-institutional-navy text-white hover:bg-institutional-navy/90 transition-colors"
          >
            <UserPlus className="w-4 h-4" />
            <span>Register New Student</span>
          </button>
        </div>
      </div>

      {/* Governance Notice */}
      <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 flex items-start space-x-3">
        <ShieldAlert className="w-5 h-5 text-institutional-navy flex-shrink-0 mt-0.5" />
        <div className="text-xs text-slate-700 leading-relaxed">
          <span className="font-semibold text-institutional-navy">
            Academic Authority Principle:
          </span>{" "}
          Academic enrolment is purely administrative. Attendance proposals never modify student
          enrolment status or cohort membership.
        </div>
      </div>

      {/* Filter / Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div className="flex items-center space-x-3 w-96">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by student name or roll number..."
            className="w-full text-sm border-none focus:outline-none placeholder-slate-400"
          />
        </div>
        <div className="flex items-center space-x-2">
          <button
            type="button"
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-50"
          >
            <Filter className="w-3.5 h-3.5" />
            <span>Filter Cohort</span>
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-6 py-3">Roll Number</th>
              <th className="px-6 py-3">Student Name</th>
              <th className="px-6 py-3">Department</th>
              <th className="px-6 py-3">Cohort</th>
              <th className="px-6 py-3">Effective Since</th>
              <th className="px-6 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {students.map((student) => (
              <tr key={student.studentId} className="hover:bg-slate-50/80 transition-colors">
                <td className="px-6 py-4 font-mono font-medium text-xs text-institutional-navy">
                  {student.rollNumber}
                </td>
                <td className="px-6 py-4 font-medium text-slate-900">
                  {student.fullName}
                </td>
                <td className="px-6 py-4 text-slate-600 text-xs">
                  {student.department}
                </td>
                <td className="px-6 py-4 text-slate-600 text-xs">
                  {student.cohort}
                </td>
                <td className="px-6 py-4 font-mono text-xs text-slate-500">
                  {student.effectiveStartDate}
                </td>
                <td className="px-6 py-4">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {student.enrollmentStatus}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
