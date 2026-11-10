"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Camera,
  Upload,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Sliders,
  ShieldCheck,
  RefreshCw,
  Eye,
  Users,
  Image as ImageIcon,
  ArrowRight,
} from "lucide-react";
import {
  analyzeDemoPhoto,
  getDemoEnrolledStudents,
  DemoAnalysisResponse,
  DemoFaceBox,
  DemoStudentResult,
  DemoEnrolledStudentSummary,
} from "@/lib/api";

export default function DemoVisualizerPage() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DemoAnalysisResponse | null>(null);
  const [enrolledCount, setEnrolledCount] = useState<number>(0);
  const [selectedFaceIdx, setSelectedFaceIdx] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<"granted" | "absent" | "strangers">("granted");

  // Threshold sliders
  const [matchThreshold, setMatchThreshold] = useState<number>(0.363);
  const [marginThreshold, setMarginThreshold] = useState<number>(0.10);
  const [blurThreshold, setBlurThreshold] = useState<number>(50.0);
  const [showConfig, setShowConfig] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getDemoEnrolledStudents().then((students) => {
      if (students) setEnrolledCount(students.length);
    });
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      setPreviewUrl(URL.createObjectURL(selected));
      setResult(null);
      setSelectedFaceIdx(null);
      triggerInference(selected);
    }
  };

  const triggerInference = async (targetFile: File) => {
    setLoading(true);
    setError(null);
    try {
      const res = await analyzeDemoPhoto(targetFile, matchThreshold, marginThreshold, blurThreshold);
      setResult(res);
      setEnrolledCount(res.total_enrolled_students);
    } catch (err: any) {
      setError(err?.message || "Failed to analyze image. Please ensure the backend server is reachable.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 mb-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Universal Ground-Truth Sandbox • Branch-Agnostic</span>
          </div>
          <h1 className="text-2xl font-serif font-bold text-slate-900 tracking-tight">
            Face Recognition Ground-Truth Inspector
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Upload any group photograph with enrolled students and unknown visitors. The system runs real YuNet
            face detection and 128-D SFace embedding extraction to visually prove who is awarded attendance and who is
            rejected without false positives.
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="px-3.5 py-2 rounded-xl text-xs font-medium border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 flex items-center space-x-2 transition shadow-sm"
          >
            <Sliders className="w-3.5 h-3.5 text-slate-500" />
            <span>{showConfig ? "Hide Calibration" : "Calibration (τ = 0.363)"}</span>
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-institutional-navy text-white hover:bg-slate-800 transition flex items-center space-x-2 shadow-sm"
          >
            <Upload className="w-4 h-4" />
            <span>Select Group Photo</span>
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={handleFileChange}
          />
        </div>
      </div>

      {/* Calibration Controls */}
      {showConfig && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 grid grid-cols-1 md:grid-cols-3 gap-6 shadow-sm">
          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
              <span>Cosine Threshold (τ)</span>
              <span className="font-mono text-emerald-600 font-bold">{matchThreshold.toFixed(3)}</span>
            </div>
            <input
              type="range"
              min="0.25"
              max="0.60"
              step="0.005"
              value={matchThreshold}
              onChange={(e) => setMatchThreshold(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
            />
            <p className="text-[11px] text-slate-500 mt-1">OpenCV Zoo SFace benchmark optimal is 0.363.</p>
          </div>
          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
              <span>Lookalike Margin (Δs)</span>
              <span className="font-mono text-amber-600 font-bold">{marginThreshold.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.05"
              max="0.25"
              step="0.01"
              value={marginThreshold}
              onChange={(e) => setMarginThreshold(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-amber-600"
            />
            <p className="text-[11px] text-slate-500 mt-1">Minimum difference between top 1 and top 2 scores.</p>
          </div>
          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
              <span>Laplacian Blur Limit</span>
              <span className="font-mono text-slate-700 font-bold">{blurThreshold.toFixed(0)}</span>
            </div>
            <input
              type="range"
              min="10"
              max="100"
              step="5"
              value={blurThreshold}
              onChange={(e) => setBlurThreshold(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-slate-700"
            />
            <p className="text-[11px] text-slate-500 mt-1">Rejects faces with variance below this limit.</p>
          </div>
        </div>
      )}

      {/* Main Grid: Photo Visualizer vs Evidence Ledger */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Augmented Photo Canvas */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h2 className="text-sm font-semibold text-slate-800 flex items-center space-x-2">
              <Camera className="w-4 h-4 text-slate-500" />
              <span>Augmented Group Photo (Visual Ground Truth)</span>
            </h2>
            {result && (
              <span className="text-xs font-mono text-slate-500">
                {result.total_detected_faces} Faces Spotted
              </span>
            )}
          </div>

          {previewUrl ? (
            <div className="relative rounded-xl overflow-hidden bg-slate-900 flex items-center justify-center min-h-[380px] max-h-[540px]">
              <img
                src={previewUrl}
                alt="Uploaded group"
                className="max-h-[540px] w-auto object-contain select-none"
              />

              {/* Bounding Box SVG Overlay */}
              {result && (
                <svg
                  className="absolute inset-0 w-full h-full pointer-events-none"
                  viewBox="0 0 100 100"
                  preserveAspectRatio="none"
                >
                  {result.detected_faces.map((face: DemoFaceBox) => {
                    const [x1, y1, x2, y2] = face.box;
                    const isSelected = selectedFaceIdx === face.face_index;
                    return (
                      <g key={face.face_index} className="pointer-events-auto cursor-pointer" onClick={() => setSelectedFaceIdx(face.face_index)}>
                        <rect
                          x={`${x1 * 100}%`}
                          y={`${y1 * 100}%`}
                          width={`${(x2 - x1) * 100}%`}
                          height={`${(y2 - y1) * 100}%`}
                          fill="none"
                          stroke={face.color_hex}
                          strokeWidth={isSelected ? "0.8" : "0.4"}
                          rx="1"
                        />
                      </g>
                    );
                  })}
                </svg>
              )}

              {/* Badges Overlay */}
              {result &&
                result.detected_faces.map((face: DemoFaceBox) => {
                  const [x1, y1] = face.box;
                  return (
                    <div
                      key={`badge-${face.face_index}`}
                      onClick={() => setSelectedFaceIdx(face.face_index)}
                      style={{
                        left: `${x1 * 100}%`,
                        top: `${Math.max(1, y1 * 100 - 4)}%`,
                        backgroundColor: face.color_hex,
                      }}
                      className="absolute transform -translate-y-full px-2 py-0.5 rounded text-[10px] font-bold text-white shadow-md cursor-pointer whitespace-nowrap z-10 transition hover:scale-105"
                    >
                      {face.badge_label}
                    </div>
                  );
                })}

              {loading && (
                <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm flex flex-col items-center justify-center text-white space-y-3 z-20">
                  <RefreshCw className="w-8 h-8 animate-spin text-emerald-400" />
                  <p className="text-sm font-semibold">Running YuNet Detection & SFace Extraction...</p>
                  <p className="text-xs text-slate-300">Searching {enrolledCount} enrolled identities in PostgreSQL</p>
                </div>
              )}
            </div>
          ) : (
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-300 hover:border-slate-400 rounded-xl p-12 text-center cursor-pointer transition bg-slate-50/50 hover:bg-slate-50"
            >
              <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mx-auto text-slate-500 mb-3">
                <ImageIcon className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-semibold text-slate-800">No Photo Selected</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Click here or use the button above to upload a classroom or group photo containing multiple students and visitors.
              </p>
              <div className="mt-4 inline-flex items-center space-x-1.5 px-3 py-1 bg-white border border-slate-200 rounded-full text-xs font-medium text-slate-600 shadow-sm">
                <Users className="w-3.5 h-3.5 text-slate-500" />
                <span>Test Gallery: {enrolledCount} Students Active</span>
              </div>
            </div>
          )}

          {/* Color Legend */}
          <div className="pt-2 flex flex-wrap items-center gap-3 text-xs border-t border-slate-100">
            <span className="inline-flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              <span className="text-slate-700 font-medium">Matched (Present)</span>
            </span>
            <span className="inline-flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
              <span className="text-slate-700 font-medium">Unknown Visitor (Not Given)</span>
            </span>
            <span className="inline-flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
              <span className="text-slate-700 font-medium">Ambiguous Lookalike</span>
            </span>
            <span className="inline-flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
              <span className="text-slate-700 font-medium">Low Quality Blur</span>
            </span>
          </div>
        </div>

        {/* Right Column: Ground-Truth Split-Screen Evidence Ledger */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col h-[640px]">
          {/* Summary Pills */}
          <div className="p-4 border-b border-slate-100 flex items-center justify-between gap-2">
            <button
              onClick={() => setActiveTab("granted")}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-semibold transition flex items-center justify-center space-x-1.5 ${
                activeTab === "granted"
                  ? "bg-emerald-50 text-emerald-800 border border-emerald-300 shadow-xs"
                  : "bg-slate-50 text-slate-600 hover:bg-slate-100"
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Granted ({result?.present_count ?? 0})</span>
            </button>
            <button
              onClick={() => setActiveTab("absent")}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-semibold transition flex items-center justify-center space-x-1.5 ${
                activeTab === "absent"
                  ? "bg-amber-50 text-amber-800 border border-amber-300 shadow-xs"
                  : "bg-slate-50 text-slate-600 hover:bg-slate-100"
              }`}
            >
              <XCircle className="w-3.5 h-3.5 text-amber-600" />
              <span>Absent ({result?.absent_count ?? 0})</span>
            </button>
            <button
              onClick={() => setActiveTab("strangers")}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-semibold transition flex items-center justify-center space-x-1.5 ${
                activeTab === "strangers"
                  ? "bg-red-50 text-red-800 border border-red-300 shadow-xs"
                  : "bg-slate-50 text-slate-600 hover:bg-slate-100"
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
              <span>Strangers ({result?.unknown_count ?? 0})</span>
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-start space-x-2">
                <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {!result && !loading && (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 p-6">
                <Eye className="w-8 h-8 text-slate-300 mb-2" />
                <p className="text-xs">Select or capture a photo to view face-by-face biometric verification.</p>
              </div>
            )}

            {/* TAB 1: ATTENDANCE GRANTED (Split-Screen Evidence) */}
            {activeTab === "granted" && result && (
              <>
                {result.attendance_granted.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-10">No enrolled students spotted in this photo.</p>
                ) : (
                  result.attendance_granted.map((item: DemoStudentResult) => (
                    <div
                      key={item.student_id}
                      className="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50/30 hover:bg-emerald-50/70 transition space-y-2.5"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-xs font-bold text-slate-900">{item.full_name}</p>
                          <p className="text-[11px] font-mono text-slate-500">{item.roll_number}</p>
                        </div>
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                          ATTENDANCE: PRESENT
                        </span>
                      </div>

                      {/* Side-by-side Evidence: Detected Crop vs Enrolled Database Portrait */}
                      <div className="flex items-center justify-between bg-white p-2.5 rounded-lg border border-emerald-100">
                        <div className="flex flex-col items-center">
                          <img
                            src={item.face_crop_base64 || ""}
                            alt="Crop"
                            className="w-12 h-12 rounded-md object-cover border border-slate-200"
                          />
                          <span className="text-[9px] text-slate-500 font-medium mt-1">Photo Crop</span>
                        </div>
                        <div className="flex flex-col items-center text-center px-2">
                          <span className="text-[11px] font-mono font-bold text-emerald-700">
                            {item.similarity_score?.toFixed(3)}
                          </span>
                          <span className="text-[8px] text-slate-400 uppercase tracking-wider">Cosine Sim</span>
                          <ArrowRight className="w-3.5 h-3.5 text-emerald-500 my-0.5" />
                        </div>
                        <div className="flex flex-col items-center">
                          <img
                            src={item.reference_photo_base64 || ""}
                            alt="Enrolled"
                            className="w-12 h-12 rounded-md object-cover border border-slate-200"
                          />
                          <span className="text-[9px] text-slate-500 font-medium mt-1">DB Reference</span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </>
            )}

            {/* TAB 2: ATTENDANCE NOT GRANTED (Absent Enrolled Students) */}
            {activeTab === "absent" && result && (
              <>
                {result.attendance_not_granted.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-10">All enrolled students are present!</p>
                ) : (
                  result.attendance_not_granted.map((item: DemoStudentResult) => (
                    <div
                      key={item.student_id}
                      className="p-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 transition flex items-center justify-between"
                    >
                      <div className="flex items-center space-x-3">
                        <img
                          src={item.reference_photo_base64 || ""}
                          alt="Enrolled"
                          className="w-10 h-10 rounded-md object-cover border border-slate-200"
                        />
                        <div>
                          <p className="text-xs font-semibold text-slate-900">{item.full_name}</p>
                          <p className="text-[11px] font-mono text-slate-500">{item.roll_number}</p>
                        </div>
                      </div>
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                        ABSENT (Not in Photo)
                      </span>
                    </div>
                  ))
                )}
              </>
            )}

            {/* TAB 3: UNIDENTIFIED STRANGERS / REJECTED FACES */}
            {activeTab === "strangers" && result && (
              <>
                {result.unidentified_faces.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-10">Zero unknown or rejected faces in photograph.</p>
                ) : (
                  result.unidentified_faces.map((face: DemoFaceBox) => (
                    <div
                      key={`unknown-${face.face_index}`}
                      className="p-3 rounded-xl border border-red-200 bg-red-50/30 space-y-2"
                    >
                      <div className="flex items-center space-x-3">
                        <img
                          src={face.face_crop_base64}
                          alt="Unknown crop"
                          className="w-11 h-11 rounded-md object-cover border border-red-200"
                        />
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-red-900">
                              Face #{face.face_index} — {face.status}
                            </span>
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-red-100 text-red-700">
                              NOT GIVEN
                            </span>
                          </div>
                          <p className="text-[10px] text-slate-600 mt-0.5">{face.badge_label}</p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
