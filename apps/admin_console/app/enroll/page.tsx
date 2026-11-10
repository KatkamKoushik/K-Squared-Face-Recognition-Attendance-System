"use client";

import React, { useState, useRef, useEffect } from "react";
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
  Image as ImageIcon,
  SwitchCamera,
  X,
} from "lucide-react";
import { submitStudentEnrollment, EnrollmentSubmissionItem } from "@/lib/api";

const DEPARTMENTS = [
  { code: "CSE", name: "Computer Science & Engineering" },
  { code: "ECE", name: "Electronics & Communication Engineering" },
  { code: "EEE", name: "Electrical & Electronics Engineering" },
  { code: "MECH", name: "Mechanical Engineering" },
  { code: "CIVIL", name: "Civil Engineering" },
  { code: "IT", name: "Information Technology" },
  { code: "CSD", name: "Computer Science & Engineering (Data Science)" },
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

  // Photo management state
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [photoSource, setPhotoSource] = useState<"camera" | "gallery" | null>(null);

  // Live web camera state
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [cameraFacingMode, setCameraFacingMode] = useState<"user" | "environment">("user");

  // Form submission state
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [submittedData, setSubmittedData] = useState<EnrollmentSubmissionItem | null>(null);

  // DOM References
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Clean up camera stream on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const startCamera = async (facing: "user" | "environment" = cameraFacingMode) => {
    setCameraError(null);
    setErrorMessage(null);

    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setCameraError("Camera access is not supported in this browser. Please upload from gallery instead.");
      return;
    }

    // Stop existing stream if already open
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: facing,
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });

      streamRef.current = stream;
      setIsCameraActive(true);

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(() => {});
      }
    } catch (err: unknown) {
      const errName = err instanceof Error ? err.name : "";
      if (errName === "NotAllowedError" || errName === "PermissionDeniedError") {
        setCameraError("Camera permission was denied. Please allow camera permissions in your browser or choose 'Upload from Gallery'.");
      } else if (errName === "NotFoundError" || errName === "DevicesNotFoundError") {
        setCameraError("No camera hardware detected. Please use 'Upload from Gallery'.");
      } else {
        setCameraError("Unable to access camera. Please select 'Upload from Gallery' instead.");
      }
      setIsCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  };

  const toggleFacingMode = () => {
    const nextMode = cameraFacingMode === "user" ? "environment" : "user";
    setCameraFacingMode(nextMode);
    startCamera(nextMode);
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;

    const width = video.videoWidth || 640;
    const height = video.videoHeight || 480;
    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    if (cameraFacingMode === "user") {
      ctx.translate(width, 0);
      ctx.scale(-1, 1);
    }
    ctx.drawImage(video, 0, 0, width, height);

    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const studentId = rollNumber.trim().toUpperCase() || "student";
        const file = new File([blob], `portrait_${studentId}.jpg`, {
          type: "image/jpeg",
          lastModified: Date.now(),
        });
        const previewUrl = URL.createObjectURL(blob);
        setPhotoFile(file);
        setPhotoPreview(previewUrl);
        setPhotoSource("camera");
        stopCamera();
      },
      "image/jpeg",
      0.95
    );
  };

  const handleGallerySelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMessage(null);
    setCameraError(null);
    if (!e.target.files || e.target.files.length === 0) return;

    const file = e.target.files[0];

    if (!file.type.startsWith("image/")) {
      setErrorMessage("Please select a valid image file (JPEG, PNG, or WebP).");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setErrorMessage("Photo size exceeds 10MB limit. Please upload an image under 10MB.");
      return;
    }

    setPhotoFile(file);
    setPhotoSource("gallery");
    const reader = new FileReader();
    reader.onload = () => {
      setPhotoPreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const clearPhoto = () => {
    setPhotoFile(null);
    setPhotoPreview(null);
    setPhotoSource(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    stopCamera();
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
      setErrorMessage("An enrollment photograph is required (either captured via camera or uploaded from gallery).");
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
      if (typeof window !== "undefined") {
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to submit enrollment application.";
      setErrorMessage(msg);
      if (typeof window !== "undefined") {
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setRollNumber("");
    setFullName("");
    setEmail("");
    setSectionCohort("");
    clearPhoto();
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
              <strong>DPDP Act 2023 Conformance</strong>: Provision of facial biometric data is governed by institutional policy. Biometric templates are extracted into mathematical embeddings (128-D vector on S¹²⁷) and raw imagery is purged in accordance with retention rules.
            </li>
            <li>
              <strong>Non-Biometric Alternative</strong>: If you withhold biometric consent, your attendance will be recorded via manual roll-call without academic penalty.
            </li>
            <li>
              <strong>Administrative Verification</strong>: All portrait submissions are reviewed by the academic department before biometric activation in the classroom roster.
            </li>
          </ul>
        </section>

        {/* Success View */}
        {submittedData ? (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 text-center space-y-6">
            <div className="w-16 h-16 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-10 h-10" />
            </div>

            <div className="space-y-2">
              <h2 className="text-2xl font-serif font-bold text-institutional-navy">
                Enrollment Application Submitted Successfully
              </h2>
              <p className="text-sm text-slate-600 max-w-lg mx-auto">
                Your photograph and academic details have been registered into the KUCET verification queue. An administrator will inspect your submission before activation.
              </p>
            </div>

            {/* Submission Receipt Card */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 text-left max-w-md mx-auto space-y-3">
              {photoPreview && (
                <div className="flex justify-center pb-3 border-b border-slate-200">
                  <img
                    src={photoPreview}
                    alt="Submitted Portrait"
                    className="w-24 h-24 rounded-xl object-cover border-2 border-emerald-500 shadow-sm"
                  />
                </div>
              )}
              <div className="flex justify-between items-center text-xs pb-3 border-b border-slate-200">
                <span className="font-semibold text-slate-500">Submission ID:</span>
                <span className="font-mono text-slate-900 font-bold">{submittedData.id}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-500">Roll Number:</span>
                <span className="font-bold text-institutional-navy">{submittedData.roll_number}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-500">Full Name:</span>
                <span className="font-medium text-slate-900">{submittedData.full_name}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-500">Department:</span>
                <span className="font-medium text-slate-900">{submittedData.department}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-500">Status:</span>
                <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800">
                  {submittedData.status}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-500">Photo Hash:</span>
                <span className="font-mono text-[10px] text-slate-600 truncate max-w-[200px]" title={submittedData.photo_sha256}>
                  {submittedData.photo_sha256}
                </span>
              </div>
            </div>

            <div className="pt-4 flex flex-wrap items-center justify-center gap-3">
              <button
                type="button"
                onClick={handleReset}
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-sm font-semibold border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors"
              >
                <RefreshCw className="w-4 h-4 text-slate-500" />
                <span>Submit Another Application</span>
              </button>
              <Link
                href="/admin/enrollment"
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-institutional-navy text-white hover:bg-institutional-navy/90 transition-colors shadow-xs"
              >
                <span>Go to Biometric Review Queue</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        ) : (
          /* Enrollment Application Form */
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-10">
            {errorMessage && (
              <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-800 flex items-start space-x-3">
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                <div className="leading-relaxed">{errorMessage}</div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Personal Identification Details */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                {/* Roll Number */}
                <div>
                  <label htmlFor="rollNumber" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Roll Number / Student ID <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
                    <input
                      id="rollNumber"
                      type="text"
                      value={rollNumber}
                      onChange={(e) => setRollNumber(e.target.value.toUpperCase())}
                      placeholder="e.g., 00622501"
                      className="w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-mono focus:outline-hidden focus:ring-2 focus:ring-institutional-navy focus:bg-white transition-all uppercase"
                      required
                    />
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Official University Roll Number (8 alphanumeric characters).</p>
                </div>

                {/* Full Student Name */}
                <div>
                  <label htmlFor="fullName" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Full Legal Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="fullName"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g., Katkam Koushik"
                    className="w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-hidden focus:ring-2 focus:ring-institutional-navy focus:bg-white transition-all"
                    required
                  />
                  <p className="text-[11px] text-slate-500 mt-1">As listed in the university admission register.</p>
                </div>
              </div>

              {/* Email Address */}
              <div>
                <label htmlFor="email" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Institutional / Student Email <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="e.g., student@kucet.ac.in"
                    className="w-full pl-9 pr-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm focus:outline-hidden focus:ring-2 focus:ring-institutional-navy focus:bg-white transition-all"
                    required
                  />
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Confirmation and review notifications will be sent here.</p>
              </div>

              {/* Academic Hierarchy */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
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

              {/* Photograph Section: Web Camera or Gallery Upload */}
              <div className="pt-2">
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    Enrollment Portrait Photograph <span className="text-red-500">*</span>
                  </label>
                  <span className="text-[11px] font-medium text-slate-500">
                    Web Options: Live Camera or Gallery Upload
                  </span>
                </div>

                {/* Hidden Inputs & Canvas */}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleGallerySelect}
                  className="hidden"
                />
                <canvas ref={canvasRef} className="hidden" />

                {/* View 1: Live Camera Active Viewfinder */}
                {isCameraActive && (
                  <div className="bg-slate-900 border-2 border-institutional-navy rounded-2xl p-4 text-center shadow-xl space-y-4">
                    <div className="flex items-center justify-between text-xs text-white pb-2 border-b border-slate-800">
                      <div className="flex items-center space-x-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
                        <span className="font-mono font-bold tracking-wider">WEB CAMERA ACTIVE</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          type="button"
                          onClick={toggleFacingMode}
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors cursor-pointer"
                          title="Switch Front/Rear Camera"
                        >
                          <SwitchCamera className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          onClick={stopCamera}
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors cursor-pointer"
                          title="Cancel Camera"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* Video Viewport with Oval Framing Guide */}
                    <div className="relative w-full max-w-sm mx-auto aspect-4/3 rounded-xl overflow-hidden bg-black shadow-inner">
                      <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted
                        className={`w-full h-full object-cover ${cameraFacingMode === "user" ? "transform scale-x-[-1]" : ""}`}
                      />
                      {/* Face Guide Overlay */}
                      <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                        <div className="w-44 h-56 border-2 border-dashed border-white/70 rounded-[50%] shadow-[0_0_0_9999px_rgba(0,0,0,0.35)]" />
                      </div>
                      <div className="absolute bottom-2 left-0 right-0 text-center pointer-events-none">
                        <span className="text-[11px] font-medium bg-black/60 text-white/90 px-3 py-1 rounded-full backdrop-blur-xs">
                          Align face within oval with neutral expression
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center justify-center space-x-3 pt-2">
                      <button
                        type="button"
                        onClick={stopCamera}
                        className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors cursor-pointer"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={capturePhoto}
                        className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-xl text-xs font-bold bg-white text-institutional-navy hover:bg-slate-100 shadow-lg hover:shadow-xl transition-all cursor-pointer"
                      >
                        <Camera className="w-4 h-4 text-institutional-navy" />
                        <span>Capture Portrait Photo</span>
                      </button>
                    </div>
                  </div>
                )}

                {/* View 2: Photo Selected / Preview */}
                {!isCameraActive && photoPreview && (
                  <div className="bg-white border-2 border-institutional-navy rounded-2xl p-6 text-center shadow-sm space-y-4">
                    <div className="relative w-40 h-48 mx-auto rounded-xl overflow-hidden shadow-md border-2 border-institutional-navy bg-slate-100">
                      <img
                        src={photoPreview}
                        alt="Enrollment Portrait Preview"
                        className="w-full h-full object-cover"
                      />
                    </div>

                    <div className="space-y-1">
                      <div className="inline-flex items-center space-x-1.5">
                        {photoSource === "camera" ? (
                          <span className="bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full text-[11px] font-bold border border-emerald-200">
                            Captured via Live Camera
                          </span>
                        ) : (
                          <span className="bg-sky-100 text-sky-800 px-3 py-1 rounded-full text-[11px] font-bold border border-sky-200">
                            Uploaded from Gallery / Files
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-slate-600 font-medium">
                        File: <span className="font-semibold text-slate-900">{photoFile?.name}</span> (
                        {Math.round((photoFile?.size || 0) / 1024)} KB)
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center justify-center gap-2 pt-2 border-t border-slate-100">
                      <button
                        type="button"
                        onClick={() => startCamera()}
                        className="inline-flex items-center space-x-1.5 px-3 py-1.5 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
                      >
                        <Camera className="w-3.5 h-3.5 text-slate-600" />
                        <span>Retake with Camera</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="inline-flex items-center space-x-1.5 px-3 py-1.5 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
                      >
                        <Upload className="w-3.5 h-3.5 text-slate-600" />
                        <span>Choose from Gallery</span>
                      </button>
                      <button
                        type="button"
                        onClick={clearPhoto}
                        className="inline-flex items-center space-x-1 px-2.5 py-1.5 text-xs font-medium text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>Remove</span>
                      </button>
                    </div>
                  </div>
                )}

                {/* View 3: Selection Hub (Web Camera vs. Gallery Upload) */}
                {!isCameraActive && !photoPreview && (
                  <div className="space-y-3">
                    {cameraError && (
                      <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-start space-x-2">
                        <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                        <span>{cameraError}</span>
                      </div>
                    )}

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {/* Option 1: Live Web Camera */}
                      <div className="bg-slate-50 border-2 border-dashed border-slate-300 hover:border-institutional-navy hover:bg-blue-50/20 rounded-2xl p-5 text-center transition-all flex flex-col items-center justify-between space-y-3">
                        <div className="w-12 h-12 rounded-xl bg-blue-100 text-institutional-navy flex items-center justify-center">
                          <Camera className="w-6 h-6" />
                        </div>
                        <div>
                          <div className="text-sm font-bold text-institutional-navy">
                            Live Web Camera
                          </div>
                          <p className="text-xs text-slate-500 mt-1">
                            Capture your frontal portrait directly using your computer or device webcam.
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => startCamera()}
                          className="w-full py-2.5 px-4 rounded-xl font-semibold text-xs bg-institutional-navy text-white hover:bg-institutional-navy/90 flex items-center justify-center space-x-1.5 transition-all shadow-xs cursor-pointer"
                        >
                          <Camera className="w-3.5 h-3.5" />
                          <span>Open Live Camera</span>
                        </button>
                      </div>

                      {/* Option 2: Upload from Gallery / Device */}
                      <div className="bg-slate-50 border-2 border-dashed border-slate-300 hover:border-sky-500 hover:bg-sky-50/20 rounded-2xl p-5 text-center transition-all flex flex-col items-center justify-between space-y-3">
                        <div className="w-12 h-12 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center">
                          <ImageIcon className="w-6 h-6" />
                        </div>
                        <div>
                          <div className="text-sm font-bold text-slate-800">
                            Upload from Gallery
                          </div>
                          <p className="text-xs text-slate-500 mt-1">
                            Select an existing portrait image file (JPEG, PNG, WebP) from your device gallery.
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => fileInputRef.current?.click()}
                          className="w-full py-2.5 px-4 rounded-xl font-semibold text-xs bg-sky-600 text-white hover:bg-sky-700 flex items-center justify-center space-x-1.5 transition-all shadow-xs cursor-pointer"
                        >
                          <Upload className="w-3.5 h-3.5" />
                          <span>Browse Photo Gallery</span>
                        </button>
                      </div>
                    </div>

                    <div className="text-center text-[11px] text-slate-500 pt-1">
                      Web-only biometric capture. Both webcam snapshot and photo gallery uploads are processed with automatic face alignment and privacy EXIF stripping.
                    </div>
                  </div>
                )}
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

              {/* Submit Error Banner */}
              {errorMessage && (
                <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-xs text-red-800 flex items-start space-x-2.5">
                  <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                  <div className="leading-relaxed font-medium">{errorMessage}</div>
                </div>
              )}

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
                      <span>Uploading to Cloudinary & Staging...</span>
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
