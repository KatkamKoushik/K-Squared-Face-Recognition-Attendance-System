"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  UserPlus,
  Search,
  Filter,
  ShieldAlert,
  Database,
  Camera,
  CheckCircle2,
  Edit3,
  Trash2,
  X,
  ShieldCheck,
  AlertCircle,
  Save,
  UserCheck,
  ImageOff,
} from "lucide-react";
import {
  getStudents,
  getDemoEnrolledStudents,
  updateStudent,
  deleteStudentPhoto,
  getStoredUser,
  StoredAuthUser,
} from "@/lib/api";
import StudentImportButton from "./StudentImportButton";

interface StudentDirectoryRow {
  studentId: string;
  rollNumber: string;
  fullName: string;
  institutionalEmail?: string;
  department: string;
  cohort: string;
  enrollmentStatus: "ACTIVE" | "ON_LEAVE" | "GRADUATED";
  effectiveStartDate: string;
  photoUrl?: string;
  hasBiometrics: boolean;
}

const DEPARTMENTS = ["ALL", "CSD", "CSE", "ECE", "MECH", "EEE", "CIVIL", "IT"];

export default function StudentsDirectoryPage() {
  const [students, setStudents] = useState<StudentDirectoryRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [departmentFilter, setDepartmentFilter] = useState("ALL");
  const [currentUser, setCurrentUser] = useState<StoredAuthUser | null>(null);

  // Edit Modal State
  const [editingStudent, setEditingStudent] = useState<StudentDirectoryRow | null>(null);
  const [editFullName, setEditFullName] = useState("");
  const [editRollNumber, setEditRollNumber] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editDepartment, setEditDepartment] = useState("CSE");
  const [editStatus, setEditStatus] = useState<"ACTIVE" | "ON_LEAVE" | "GRADUATED">("ACTIVE");
  const [savingEdit, setSavingEdit] = useState(false);

  // Delete Photo Confirmation Modal State
  const [deletingPhotoStudent, setDeletingPhotoStudent] = useState<StudentDirectoryRow | null>(null);
  const [deletingPhoto, setDeletingPhoto] = useState(false);

  // Feedback Notification
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    setCurrentUser(getStoredUser());
    loadDirectory();
  }, []);

  const isDeveloper = useMemo(() => {
    if (!currentUser) return false;
    const email = (currentUser.email || "").toLowerCase().trim();
    return email === "koushikkatkam@gmail.com" || currentUser.role === "DEVELOPER";
  }, [currentUser]);

  const loadDirectory = async () => {
    setLoading(true);
    try {
      const [serverStudents, enrolledBiometrics] = await Promise.all([
        getStudents().catch(() => null),
        getDemoEnrolledStudents().catch(() => null),
      ]);

      const bioMap = new Map((enrolledBiometrics || []).map((b) => [b.roll_number, b]));

      const rawList =
        serverStudents && serverStudents.length > 0
          ? serverStudents.map((s) => ({
              id: s.id,
              roll_number: s.roll_number,
              full_name: s.full_name,
              institutional_email: s.institutional_email,
              current_term: s.current_term,
              status: s.status,
              enrollment_date: s.enrollment_date,
            }))
          : (enrolledBiometrics || []).map((b) => ({
              id: b.student_id,
              roll_number: b.roll_number,
              full_name: b.full_name,
              institutional_email: `${b.roll_number.toLowerCase()}@kucet.ac.in`,
              current_term: 8,
              status: b.is_active ? "ACTIVE" : "INACTIVE",
              enrollment_date: "2023-08-01",
            }));

      const rows: StudentDirectoryRow[] = rawList.map((s) => {
        const bio = bioMap.get(s.roll_number);
        const deptCode = bio?.department_code || "CSE";
        return {
          studentId: s.id,
          rollNumber: s.roll_number,
          fullName: s.full_name,
          institutionalEmail: s.institutional_email,
          department: deptCode,
          cohort: `Term ${s.current_term || 8}`,
          enrollmentStatus: (s.status as any) || "ACTIVE",
          effectiveStartDate: s.enrollment_date || "2023-08-01",
          photoUrl: bio?.photo_url,
          hasBiometrics: Boolean(bio),
        };
      });

      setStudents(rows);
    } catch {
      setFeedback({ type: "error", text: "Failed to load student directory from control plane." });
    } finally {
      setLoading(false);
    }
  };

  const filteredStudents = useMemo(() => {
    return students.filter((s) => {
      const matchSearch =
        searchTerm === "" ||
        s.fullName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.rollNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (s.institutionalEmail || "").toLowerCase().includes(searchTerm.toLowerCase());

      const matchDept = departmentFilter === "ALL" || s.department.toUpperCase() === departmentFilter.toUpperCase();

      return matchSearch && matchDept;
    });
  }, [students, searchTerm, departmentFilter]);

  const handleOpenEdit = (student: StudentDirectoryRow) => {
    setEditingStudent(student);
    setEditFullName(student.fullName);
    setEditRollNumber(student.rollNumber);
    setEditEmail(student.institutionalEmail || "");
    setEditDepartment(student.department || "CSE");
    setEditStatus(student.enrollmentStatus);
    setFeedback(null);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingStudent) return;

    setSavingEdit(true);
    setFeedback(null);

    try {
      const res = await updateStudent(editingStudent.studentId, {
        full_name: editFullName.trim(),
        roll_number: editRollNumber.trim(),
        institutional_email: editEmail.trim() || undefined,
        department_code: editDepartment,
        status: editStatus,
      });

      if (res) {
        setStudents((prev) =>
          prev.map((s) =>
            s.studentId === editingStudent.studentId
              ? {
                  ...s,
                  fullName: editFullName.trim(),
                  rollNumber: editRollNumber.trim(),
                  institutionalEmail: editEmail.trim(),
                  department: editDepartment,
                  enrollmentStatus: editStatus,
                }
              : s
          )
        );
        setFeedback({
          type: "success",
          text: `Student record ${editRollNumber} successfully updated by Developer in PostgreSQL database.`,
        });
        setEditingStudent(null);
      } else {
        setFeedback({ type: "error", text: "Failed to update student. Ensure backend service is reachable." });
      }
    } catch (err: any) {
      setFeedback({ type: "error", text: err.message || "Failed to update student record." });
    } finally {
      setSavingEdit(false);
    }
  };

  const handleConfirmDeletePhoto = async () => {
    if (!deletingPhotoStudent) return;

    setDeletingPhoto(true);
    setFeedback(null);

    try {
      const res = await deleteStudentPhoto(deletingPhotoStudent.studentId);
      if (res && res.success) {
        setStudents((prev) =>
          prev.map((s) =>
            s.studentId === deletingPhotoStudent.studentId
              ? {
                  ...s,
                  photoUrl: undefined,
                  hasBiometrics: false,
                }
              : s
          )
        );
        setFeedback({
          type: "success",
          text: `Biometric photos and face embeddings for ${deletingPhotoStudent.rollNumber} successfully deleted from database.`,
        });
        setDeletingPhotoStudent(null);
      } else {
        setFeedback({ type: "error", text: "Failed to delete student photo from database." });
      }
    } catch (err: any) {
      setFeedback({ type: "error", text: err.message || "Photo purge failed." });
    } finally {
      setDeletingPhoto(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl font-bold text-institutional-navy">
            Student Directory & Biometric Enrolment Registry
          </h1>
          <p className="text-sm text-institutional-muted">
            Authoritative student registry, registered facial portraits, and multi-model embedding status.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-full border bg-white shadow-xs">
            <Database className="w-3.5 h-3.5 text-emerald-600" />
            <span className="text-emerald-700 font-mono">LIVE ACADEMIC REGISTRY</span>
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

      {/* Developer Exclusive Privilege Banner */}
      {isDeveloper ? (
        <div className="bg-emerald-50/90 border-2 border-emerald-500/40 rounded-xl p-4 flex items-start space-x-3 shadow-xs">
          <ShieldCheck className="w-5 h-5 text-emerald-700 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-emerald-950 leading-relaxed flex-1">
            <div className="font-bold text-emerald-900 text-sm flex items-center space-x-2">
              <span>Developer Absolute Control Active</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-200 text-emerald-900">
                koushikkatkam@gmail.com
              </span>
            </div>
            <p className="mt-0.5 text-emerald-800">
              You possess unrestricted, absolute permission to rewrite student names, alter roll numbers, reassign departments, and permanently purge biometric photographs and face embeddings from the PostgreSQL database.
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 flex items-start space-x-3">
          <ShieldAlert className="w-5 h-5 text-institutional-navy flex-shrink-0 mt-0.5" />
          <div className="text-xs text-slate-700 leading-relaxed">
            <span className="font-semibold text-institutional-navy">Academic Authority Principle:</span> Academic enrolment is purely administrative. Attendance proposals never modify student enrolment status or cohort membership.
          </div>
        </div>
      )}

      {/* Feedback Toast */}
      {feedback && (
        <div
          className={`p-3.5 rounded-xl border flex items-center justify-between text-xs font-medium ${
            feedback.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-red-50 border-red-200 text-red-800"
          }`}
        >
          <div className="flex items-center space-x-2">
            {feedback.type === "success" ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
            )}
            <span>{feedback.text}</span>
          </div>
          <button
            onClick={() => setFeedback(null)}
            className="text-slate-400 hover:text-slate-600 transition-colors p-1"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Filter / Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-3 w-full md:w-96 bg-slate-50 border border-slate-200 px-3 py-2 rounded-xl">
          <Search className="w-4 h-4 text-slate-400 shrink-0" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search student name, roll number, or email..."
            className="w-full text-xs border-none bg-transparent focus:outline-hidden placeholder-slate-400 text-slate-800"
          />
          {searchTerm && (
            <button onClick={() => setSearchTerm("")} className="text-slate-400 hover:text-slate-600">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center space-x-2 flex-wrap">
          <span className="text-xs font-semibold text-slate-500">Dept:</span>
          <div className="flex space-x-1 overflow-x-auto">
            {DEPARTMENTS.map((dept) => {
              const isSelected = departmentFilter === dept;
              return (
                <button
                  key={dept}
                  type="button"
                  onClick={() => setDepartmentFilter(dept)}
                  className={`px-2.5 py-1 text-xs rounded-lg font-semibold transition-colors ${
                    isSelected
                      ? "bg-institutional-navy text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {dept}
                </button>
              );
            })}
          </div>

          <Link
            href="/demo"
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 border border-emerald-300 rounded-lg text-xs font-semibold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 transition shadow-xs"
          >
            <Camera className="w-3.5 h-3.5 text-emerald-600" />
            <span>Face Visualizer</span>
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

      {/* Student Directory Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-6 py-3">Portrait</th>
              <th className="px-6 py-3">Roll Number</th>
              <th className="px-6 py-3">Student Name</th>
              <th className="px-6 py-3">Department</th>
              <th className="px-6 py-3">Biometrics Status</th>
              <th className="px-6 py-3">Lifecycle</th>
              {isDeveloper && <th className="px-6 py-3 text-right">Developer Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {loading ? (
              <tr>
                <td colSpan={isDeveloper ? 7 : 6} className="px-6 py-12 text-center text-slate-500 text-xs">
                  <div className="flex flex-col items-center justify-center space-y-2">
                    <div className="w-6 h-6 border-2 border-institutional-navy border-t-transparent rounded-full animate-spin" />
                    <span>Loading student records from PostgreSQL database...</span>
                  </div>
                </td>
              </tr>
            ) : filteredStudents.length === 0 ? (
              <tr>
                <td colSpan={isDeveloper ? 7 : 6} className="px-6 py-12 text-center text-slate-500 text-xs">
                  No enrolled student records found matching the filter criteria.
                </td>
              </tr>
            ) : (
              filteredStudents.map((student) => (
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
                  <td className="px-6 py-4">
                    <div className="font-semibold text-slate-900 text-xs">{student.fullName}</div>
                    {student.institutionalEmail && (
                      <div className="text-[11px] text-slate-400 font-mono">{student.institutionalEmail}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-slate-600 text-xs">
                    <span className="px-2 py-0.5 rounded font-semibold bg-slate-100 text-slate-700">
                      {student.department}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {student.hasBiometrics ? (
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        <span>Multi-Model Enrolled</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-amber-50 text-amber-800 border border-amber-200">
                        <AlertCircle className="w-3 h-3 text-amber-600" />
                        <span>No Biometrics (Purged)</span>
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                        student.enrollmentStatus === "ACTIVE"
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {student.enrollmentStatus}
                    </span>
                  </td>

                  {/* Developer Controls: Edit Name / Details + Delete Photo */}
                  {isDeveloper && (
                    <td className="px-6 py-4 text-right">
                      <div className="inline-flex items-center space-x-1.5">
                        <button
                          type="button"
                          onClick={() => handleOpenEdit(student)}
                          title="Rewrite student name & details in database"
                          className="inline-flex items-center space-x-1 px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition-colors shadow-xs"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                          <span>Rewrite</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => setDeletingPhotoStudent(student)}
                          disabled={!student.hasBiometrics && !student.photoUrl}
                          title="Delete photo & biometric embeddings from database"
                          className="inline-flex items-center space-x-1 px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition-colors shadow-xs disabled:opacity-30 disabled:pointer-events-none"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>Delete Photo</span>
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Edit Student Modal (Developer Exclusive) */}
      {editingStudent && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 space-y-5 border border-slate-200 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center space-x-2">
                <div className="p-2 rounded-lg bg-institutional-navy text-white">
                  <Edit3 className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-base text-institutional-navy">
                    Rewrite Student Database Record
                  </h3>
                  <p className="text-xs text-slate-500 font-mono">
                    Developer authority: koushikkatkam@gmail.com
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setEditingStudent(null)}
                className="text-slate-400 hover:text-slate-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveEdit} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Student Full Name (Rewrite)
                </label>
                <input
                  type="text"
                  required
                  value={editFullName}
                  onChange={(e) => setEditFullName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-institutional-navy focus:outline-hidden text-sm font-medium"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Roll Number / Student ID
                </label>
                <input
                  type="text"
                  required
                  value={editRollNumber}
                  onChange={(e) => setEditRollNumber(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-institutional-navy focus:outline-hidden text-sm font-mono font-bold"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Institutional Email
                </label>
                <input
                  type="email"
                  value={editEmail}
                  onChange={(e) => setEditEmail(e.target.value)}
                  placeholder="student@kucet.ac.in"
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-institutional-navy focus:outline-hidden text-sm font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Department
                  </label>
                  <select
                    value={editDepartment}
                    onChange={(e) => setEditDepartment(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-institutional-navy focus:outline-hidden text-sm bg-white"
                  >
                    {DEPARTMENTS.filter((d) => d !== "ALL").map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Lifecycle Status
                  </label>
                  <select
                    value={editStatus}
                    onChange={(e) => setEditStatus(e.target.value as any)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-institutional-navy focus:outline-hidden text-sm bg-white"
                  >
                    <option value="ACTIVE">ACTIVE</option>
                    <option value="ON_LEAVE">ON_LEAVE</option>
                    <option value="GRADUATED">GRADUATED</option>
                  </select>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-200 flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setEditingStudent(null)}
                  className="px-4 py-2 border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingEdit}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 bg-institutional-navy text-white rounded-xl text-xs font-bold hover:bg-institutional-navy/90 transition-colors shadow-sm disabled:opacity-50"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>{savingEdit ? "Saving in Database..." : "Commit Changes"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Photo Confirmation Modal (Developer Exclusive) */}
      {deletingPhotoStudent && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 border border-slate-200 shadow-2xl">
            <div className="flex items-center space-x-3 text-red-600">
              <div className="p-2 rounded-xl bg-red-100">
                <ImageOff className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <h3 className="font-bold text-base text-slate-900">Delete Photo from Database?</h3>
                <p className="text-xs text-slate-500 font-mono">
                  Permanent deletion of biometric face embeddings
                </p>
              </div>
            </div>

            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-900 space-y-1">
              <p className="font-semibold">
                Student: {deletingPhotoStudent.fullName} ({deletingPhotoStudent.rollNumber})
              </p>
              <p className="text-red-700 leading-relaxed">
                This will purge all extracted face embedding vectors across Option 1 (512-D), Option 3 (128-D), and Fine-Tuned models from PostgreSQL and clear the reference photo path.
              </p>
            </div>

            <div className="pt-2 flex items-center justify-end space-x-3 text-xs">
              <button
                type="button"
                onClick={() => setDeletingPhotoStudent(null)}
                className="px-4 py-2 border border-slate-300 rounded-xl font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={deletingPhoto}
                onClick={handleConfirmDeletePhoto}
                className="inline-flex items-center space-x-1.5 px-4 py-2 bg-red-600 text-white rounded-xl font-bold hover:bg-red-700 transition-colors shadow-sm disabled:opacity-50"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>{deletingPhoto ? "Deleting from Database..." : "Confirm Delete Photo"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
