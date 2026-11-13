import React from "react";
import Link from "next/link";
import { UserPlus, Search, Filter, ShieldAlert, Database, Camera, CheckCircle2 } from "lucide-react";
import { getStudents, getDemoEnrolledStudents } from "@/lib/api";
import StudentImportButton from "./StudentImportButton";

interface StudentDirectoryRow {
  studentId: string;
  rollNumber: string;
  fullName: string;
  department: string;
  cohort: string;
  enrollmentStatus: "ACTIVE" | "ON_LEAVE" | "GRADUATED";
  effectiveStartDate: string;
  photoUrl?: string;
  hasBiometrics: boolean;
}

export default async function StudentsDirectoryPage() {
  const [serverStudents, enrolledBiometrics] = await Promise.all([
    getStudents(),
    getDemoEnrolledStudents().catch(() => null),
  ]);

  const isLive = serverStudents !== null;
  const bioMap = new Map((enrolledBiometrics || []).map((b) => [b.roll_number, b]));

  const rawList =
    serverStudents && serverStudents.length > 0
      ? serverStudents.map((s) => ({
          id: s.id,
          roll_number: s.roll_number,
          full_name: s.full_name,
          current_term: s.current_term,
          status: s.status,
          enrollment_date: s.enrollment_date,
        }))
      : (enrolledBiometrics || []).map((b) => ({
          id: b.student_id,
          roll_number: b.roll_number,
          full_name: b.full_name,
          current_term: 8,
          status: b.is_active ? "ACTIVE" : "INACTIVE",
          enrollment_date: "2023-08-01",
        }));

  const students: StudentDirectoryRow[] = rawList.map((s) => {
    const bio = bioMap.get(s.roll_number);
    return {
      studentId: s.id,
      rollNumber: s.roll_number,
      fullName: s.full_name,
      department: bio?.department_code ? `${bio.department_code} Department` : "Computer Science & Engineering",
      cohort: `Term ${s.current_term}`,
      enrollmentStatus: (s.status as any) || "ACTIVE",
      effectiveStartDate: s.enrollment_date || "2023-08-01",
      photoUrl: bio?.photo_url,
      hasBiometrics: Boolean(bio),
    };
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl font-bold text-institutional-navy">
            Student Directory & Biometric Enrolment Registry
          </h1>
          <p className="text-sm text-institutional-muted">
            Authoritative student registry, registered facial portraits, and 128-D SFace feature template status.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-full border bg-white shadow-xs">
            <Database className={`w-3.5 h-3.5 ${isLive ? "text-emerald-600" : "text-slate-400"}`} />
            <span className={isLive ? "text-emerald-700 font-mono" : "text-slate-600"}>
              {isLive ? "LIVE ACADEMIC REGISTRY" : "REGISTRY SNAPSHOT"}
            </span>
          </div>
          <StudentImportButton />
          <Link
            href="/enroll"
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium bg-institutional-navy text-white hover:bg-institutional-navy/90 transition-colors shadow-xs"
          >
            <UserPlus className="w-4 h-4" />
            <span>Register New Student</span>
          </Link>
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
          enrolment status or cohort membership. All facial templates are stored as 128-D hyperspherical vectors.
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
          <Link
            href="/demo"
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 border border-emerald-300 rounded-lg text-xs font-semibold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 transition shadow-xs"
          >
            <Camera className="w-3.5 h-3.5 text-emerald-600" />
            <span>Open Demo Face Visualizer</span>
          </Link>
          <Link
            href="/admin/enrollment"
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-50 transition shadow-xs"
          >
            <Filter className="w-3.5 h-3.5" />
            <span>Biometric Queue</span>
          </Link>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-6 py-3">Portrait</th>
              <th className="px-6 py-3">Roll Number</th>
              <th className="px-6 py-3">Student Name</th>
              <th className="px-6 py-3">Department</th>
              <th className="px-6 py-3">Cohort</th>
              <th className="px-6 py-3">Biometrics</th>
              <th className="px-6 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {students.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-slate-500 text-xs">
                  No enrolled student records found in database. Students appear here after biometric application review and approval.
                </td>
              </tr>
            ) : (
              students.map((student) => (
                <tr key={student.studentId} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-6 py-3">
                    <div className="relative w-11 h-11 rounded-xl overflow-hidden border border-slate-200 bg-slate-100 flex items-center justify-center shrink-0 shadow-xs">
                      {student.photoUrl ? (
                        <img
                          src={student.photoUrl}
                          alt={student.fullName}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center font-bold text-xs text-slate-500 bg-slate-200">
                          {student.fullName.slice(0, 2).toUpperCase()}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 font-mono font-bold text-xs text-institutional-navy">
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
                  <td className="px-6 py-4">
                    {student.hasBiometrics ? (
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        <span>128-D Enrolled</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-600">
                        <span>No Biometrics</span>
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {student.enrollmentStatus}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
