"use client";

import React, { useState, useRef } from "react";
import Link from "next/link";
import {
  Shield,
  Upload,
  CheckCircle2,
  AlertCircle,
  FileText,
  User,
  Mail,
  Building,
  Calendar,
  Lock,
  ArrowRight,
  Info,
  RefreshCw,
  Camera,
} from "lucide-react";
import { submitStudentEnrollment, EnrollmentSubmissionItem } from "@/lib/api";

const DEPARTMENTS = [
  { code: "CSE", name: "Computer Science & Engineering" },
  { code: "ECE", name: "Electronics & Communication Engineering" },
  { code: "EEE", name: "Electrical & Electronics Engineering" },
  { code: "MECH", name: "Mechanical Engineering" },
  { code: "CIVIL", name: "Civil Engineering" },
  { code: "IT", name: "Information Technology" },
];

const ACADEMIC_YEARS = [
  "2024-2028 (I Year)",
  "2023-2027 (II Year)",
  "2022-2026 (III Year)",
  "2021-2025 (IV Year)",
];

export default function StudentEnrollmentPage() {
  const [rollNumber, setRollNumber] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [department, setDepartment] = useState("CSE");
  const [academicYear, setAcademicYear] = useState(ACADEMIC_YEARS[2]);
  const [sectionCohort, setSectionCohort] = useState("");
  const [consentAcknowledged, setConsentAcknowledged] = useState(false);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [submittedData, setSubmittedData] = useState<EnrollmentSubmissionItem | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handlePhotoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMessage(null);
    if (!e.target.files || e.target.files.length === 0) return;

    const file = e.target.files[0];

    // Basic client checks
    if (!file.type.startsWith("image/")) {
      setErrorMessage("Please select a valid image file (JPEG, PNG, or WebP).");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setErrorMessage("Photo size exceeds 10MB limit. Please upload an image under 10MB.");
      return;
    }

    setPhotoFile(file);
    const reader = new FileReader();
    reader.onload = () => {
      setPhotoPreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!rollNumber.trim()) {
      setErrorMessage("Institutional Roll Number / Student ID is required.");
      return;
    }

    if (!fullName.trim()) {
      setErrorMessage("Full student name is required.");
      return;
    }

    if (!email.trim() || !email.includes("@")) {
      setErrorMessage("A valid institutional or official email address is required.");
      return;
    }

    if (!photoFile) {
      setErrorMessage("An enrollment photograph is required.");
      return;
    }

    if (!consentAcknowledged) {
      setErrorMessage("You must acknowledge the biometric notice and consent policy to submit.");
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("roll_number", rollNumber.trim().toUpperCase());
      formData.append("full_name", fullName.trim());
      formData.append("institutional_email", email.trim().toLowerCase());
      formData.append("department", department);
      formData.append("academic_year", academicYear);
      if (sectionCohort.trim()) {
        formData.append("cohort_id", sectionCohort.trim());
      }
      formData.append("consent_acknowledged", "true");
      formData.append("photo", photoFile);

      const response = await submitStudentEnrollment(formData);
      setSubmittedData(response);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to submit enrollment application.";
      setErrorMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setRollNumber("");
    setFullName("");
    setEmail("");
    setSectionCohort("");
    setPhotoFile(null);
    setPhotoPreview(null);
    setConsentAcknowledged(false);
    setSubmittedData(null);
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Top Navigation Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-institutional-navy flex items-center justify-center text-white font-serif font-bold text-lg shadow-sm">
              K²
            </div>
            <div>
              <div className="text-sm font-bold text-institutional-navy font-serif leading-tight">
                Kakatiya University College of Engineering & Technology
              </div>
              <div className="text-[11px] text-slate-500 font-medium">
                KUCET Warangal • Student Biometric Enrollment Portal (FRS V7.1)
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Link
              href="/admin"
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg text-slate-700 hover:text-institutional-navy hover:bg-slate-100 transition-colors"
            >
              <Lock className="w-3.5 h-3.5 text-slate-500" />
              <span>Admin & Faculty Portal</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Headline */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-institutional-blue border border-blue-200 mb-3">
            <Shield className="w-3.5 h-3.5" />
            <span>Official University Attendance Registration</span>
          </div>
          <h1 className="text-3xl font-serif font-bold text-institutional-navy">
            Student Biometric Attendance Enrollment
          </h1>
          <p className="mt-2 text-sm text-slate-600 max-w-2xl mx-auto">
            Submit your student details and high-resolution frontal portrait to enroll in the
            automated classroom attendance recognition workflow for your registered subject offerings.
          </p>
        </div>

        {/* Institutional Governance & Notice Banner */}
        <section aria-labelledby="biometric-notice-title" className="mb-8 bg-amber-50/70 border border-amber-200 rounded-2xl p-5 text-amber-950 text-xs space-y-2">
          <div className="flex items-center space-x-2 font-semibold text-amber-900 text-sm">
            <Info className="w-4 h-4 text-amber-700 shrink-0" />
            <span id="biometric-notice-title">Notice Concerning Biometric Attendance Enrollment</span>
          </div>
          <ul className="list-disc list-inside space-y-1.5 pl-1 text-slate-700">
            <li>
              <strong>Purpose of Collection:</strong> Your enrollment photograph is used solely to generate a
              128-dimensional facial representation vector for automated attendance verification in conducted class units.
            </li>
            <li>
              <strong>Verification & Approval:</strong> Submitted portraits are stored in encrypted, private storage and
              must be reviewed by designated academic administrators before reference template activation.
            </li>
            <li>
              <strong>Voluntary Participation & Manual Attendance:</strong> Use of face recognition is voluntary. Per
              university policy, manual faculty attendance sign-in remains unconditionally available for any student without penalty.
            </li>
            <li>
              <strong>Rights & Withdrawal:</strong> You may request review, correction, or withdrawal of your reference
              biometric template at any time by contacting your department administrative office.
            </li>
          </ul>
        </section>

        {/* Submission Successful Confirmation View */}
        {submittedData ? (
          <div className="bg-white rounded-2xl border border-emerald-200 shadow-sm p-8 text-center space-y-6">
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto text-emerald-600">
              <CheckCircle2 className="w-10 h-10" />
            </div>
            <div>
              <h2 className="text-2xl font-serif font-bold text-slate-900">
                Enrollment Application Submitted
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                Your photograph and student record have been securely staged for administrative verification.
              </p>
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 max-w-md mx-auto text-left text-xs space-y-2.5">
              <div className="flex justify-between border-b border-slate-200 pb-2">
                <span className="text-slate-500">Roll Number:</span>
                <span className="font-bold text-slate-900 font-mono">{submittedData.roll_number}</span>
              </div>
              <div className="flex justify-between border-b border-slate-200 pb-2">
                <span className="text-slate-500">Student Name:</span>
                <span className="font-semibold text-slate-900">{submittedData.full_name}</span>
              </div>
              <div className="flex justify-between border-b border-slate-200 pb-2">
                <span className="text-slate-500">Department:</span>
                <span className="font-medium text-slate-800">{submittedData.department}</span>
              </div>
              <div className="flex justify-between border-b border-slate-200 pb-2">
                <span className="text-slate-500">Enrollment Status:</span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800">
                  {submittedData.status}
                </span>
              </div>
              <div className="flex justify-between pt-1">
                <span className="text-slate-500">Photo SHA-256:</span>
                <span className="font-mono text-[10px] text-slate-600 truncate max-w-[200px]" title={submittedData.photo_sha256}>
                  {submittedData.photo_sha256.substring(0, 16)}...
                </span>
              </div>
            </div>

            <div className="text-xs text-slate-500 max-w-md mx-auto">
              A department administrator will review your portrait quality and approve your face template for
              inclusion in your class rosters.
            </div>

            <div className="pt-2">
              <button
                type="button"
                onClick={handleReset}
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-institutional-navy text-white hover:bg-institutional-navy/90 transition-colors shadow-sm"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Submit Another Enrollment</span>
              </button>
            </div>
          </div>
        ) : (
          /* Enrollment Form */
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
            {errorMessage && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold">Submission Validation Error</div>
                  <div className="text-xs mt-0.5">{errorMessage}</div>
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                {/* Roll Number */}
                <div>
                  <label htmlFor="rollNumber" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Institutional Roll Number <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
                    <input
                      id="rollNumber"
                      type="text"
                      required
                      value={rollNumber}
                      onChange={(e) => setRollNumber(e.target.value)}
                      placeholder="e.g., 22016A0501"
                      className="w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-mono focus:outline-hidden focus:ring-2 focus:ring-institutional-navy focus:bg-white transition-all uppercase"
                    />
                  </div>
                </div>

                {/* Full Name */}
                <div>
                  <label htmlFor="fullName" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Full Student Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="fullName"
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g., Katkam Koushik"
                    className="w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-hidden focus:ring-2 focus:ring-institutional-navy focus:bg-white transition-all"
                  />
                </div>

                {/* Email */}
                <div>
                  <label htmlFor="email" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Institutional Email Address <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
                    <input
                      id="email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="student@kucet.ac.in"
                      className="w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-hidden focus:ring-2 focus:ring-institutional-navy focus:bg-white transition-all"
                    />
                  </div>
                </div>

                {/* Department */}
                <div>
                  <label htmlFor="department" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Academic Department <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Building className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
                    <select
                      id="department"
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      className="w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-hidden focus:ring-2 focus:ring-institutional-navy focus:bg-white transition-all"
                    >
                      {DEPARTMENTS.map((d) => (
                        <option key={d.code} value={d.code}>
                          {d.code} — {d.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Academic Year */}
                <div>
                  <label htmlFor="academicYear" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Academic Year / Batch <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Calendar className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
                    <select
                      id="academicYear"
                      value={academicYear}
                      onChange={(e) => setAcademicYear(e.target.value)}
                      className="w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-hidden focus:ring-2 focus:ring-institutional-navy focus:bg-white transition-all"
                    >
                      {ACADEMIC_YEARS.map((y) => (
                        <option key={y} value={y}>
                          {y}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Section / Cohort */}
                <div>
                  <label htmlFor="sectionCohort" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Section / Cohort ID (Optional)
                  </label>
                  <input
                    id="sectionCohort"
                    type="text"
                    value={sectionCohort}
                    onChange={(e) => setSectionCohort(e.target.value)}
                    placeholder="e.g., Section A or Cohort UUID"
                    className="w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-hidden focus:ring-2 focus:ring-institutional-navy focus:bg-white transition-all"
                  />
                </div>
              </div>

              {/* Photograph Upload Section */}
              <div className="pt-2">
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Enrollment Portrait Photograph <span className="text-red-500">*</span>
                </label>
                <div className="border-2 border-dashed border-slate-300 hover:border-institutional-navy rounded-2xl p-6 text-center transition-all bg-slate-50/50">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    capture="user"
                    onChange={handlePhotoSelect}
                    className="hidden"
                  />

                  {photoPreview ? (
                    <div className="space-y-4">
                      <div className="relative w-40 h-48 mx-auto rounded-xl overflow-hidden shadow-md border-2 border-institutional-navy">
                        <img
                          src={photoPreview}
                          alt="Enrollment Portrait Preview"
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="text-xs text-slate-600 font-medium">
                        Selected: <span className="font-semibold text-slate-900">{photoFile?.name}</span> (
                        {Math.round((photoFile?.size || 0) / 1024)} KB)
                      </div>
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="inline-flex items-center space-x-1.5 px-3 py-1.5 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors"
                      >
                        <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
                        <span>Choose Different Photo</span>
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="w-12 h-12 bg-blue-50 text-institutional-blue rounded-xl flex items-center justify-center mx-auto">
                        <Camera className="w-6 h-6" />
                      </div>
                      <div>
                        <button
                          type="button"
                          onClick={() => fileInputRef.current?.click()}
                          className="text-sm font-semibold text-institutional-blue hover:text-institutional-navy underline decoration-2 underline-offset-2"
                        >
                          Upload a photo or capture with camera
                        </button>
                        <p className="text-xs text-slate-500 mt-1">
                          PNG, JPG, or WebP up to 10MB. Must be a clear frontal portrait with good lighting.
                        </p>
                      </div>
                      <div className="text-[11px] text-slate-400 bg-white inline-block px-3 py-1 rounded-md border border-slate-200">
                        Face detection runs automatically on upload. EXIF & GPS metadata will be stripped.
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Consent Acknowledgement */}
              <div className="pt-2">
                <label className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={consentAcknowledged}
                    onChange={(e) => setConsentAcknowledged(e.target.checked)}
                    className="w-4 h-4 rounded-md border-slate-300 text-institutional-navy focus:ring-institutional-navy mt-0.5"
                  />
                  <span className="text-xs text-slate-700 leading-relaxed">
                    I acknowledge that this photograph will be used exclusively for automated classroom attendance
                    verification at KU College of Engineering & Technology. I understand that my reference template
                    requires administrative verification, and that manual attendance sign-in remains available per
                    institutional regulations without academic penalty.
                  </span>
                </label>
              </div>

              {/* Submit Button */}
              <div className="pt-4 border-t border-slate-200 flex items-center justify-between">
                <div className="text-xs text-slate-500">
                  Protected under KUCET Academic Biometric Governance Policy
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl text-sm font-semibold bg-institutional-navy text-white hover:bg-institutional-navy/90 disabled:opacity-50 transition-all shadow-md hover:shadow-lg cursor-pointer"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Validating & Staging...</span>
                    </>
                  ) : (
                    <>
                      <span>Submit Biometric Application</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="mt-16 border-t border-slate-200 bg-white py-8 text-center text-xs text-slate-500">
        <div className="max-w-4xl mx-auto px-4 space-y-2">
          <div>
            FRS V7.1 K² — Face Recognition Attendance System • Kakatiya University College of Engineering & Technology
          </div>
          <div>
            Authoritative Ledger: PostgreSQL • Face Inference: OpenCV Zoo YuNet & SFace ONNX
          </div>
        </div>
      </footer>
    </div>
  );
}
