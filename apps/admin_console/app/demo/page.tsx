"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import Link from "next/link";
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
  Database,
  Sparkles,
  ExternalLink,
  Layers,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Plus,
  Trash2,
  Check,
} from "lucide-react";
import {
  analyzeDemoPhoto,
  getDemoEnrolledStudents,
  DemoAnalysisResponse,
  DemoFaceBox,
  DemoStudentResult,
  DemoEnrolledStudentSummary,
} from "@/lib/api";

export interface SweepFrame {
  id: string;
  name: string;
  file: File;
  previewUrl: string;
  result: DemoAnalysisResponse | null;
  loading: boolean;
  error: string | null;
}

export type OverlayDisplayMode = "clean" | "boxesOnly" | "rawPhoto";

export default function DemoVisualizerPage() {
  const [frames, setFrames] = useState<SweepFrame[]>([]);
  const [activeFrameIdx, setActiveFrameIdx] = useState<number>(0);
  const [overlayMode, setOverlayMode] = useState<OverlayDisplayMode>("clean");
  const [selectedFaceIdx, setSelectedFaceIdx] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<"granted" | "absent" | "strangers">("granted");
  const [zoomLevel, setZoomLevel] = useState<number>(1.0);

  // Calibration thresholds (calibrated to OpenCV Zoo SFace & YuNet defaults)
  const [matchThreshold, setMatchThreshold] = useState<number>(0.363);
  const [marginThreshold, setMarginThreshold] = useState<number>(0.10);
  const [blurThreshold, setBlurThreshold] = useState<number>(20.0);
  const [selectedDepartment, setSelectedDepartment] = useState<string>("ALL");
  const [showConfig, setShowConfig] = useState(false);

  // Gallery
  const [enrolledStudents, setEnrolledStudents] = useState<DemoEnrolledStudentSummary[]>([]);
  const [enrolledLoading, setEnrolledLoading] = useState<boolean>(true);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadEnrolledGallery(selectedDepartment);
  }, [selectedDepartment]);

  const loadEnrolledGallery = async (dept: string = selectedDepartment) => {
    setEnrolledLoading(true);
    try {
      const students = await getDemoEnrolledStudents(dept);
      if (students) {
        setEnrolledStudents(students);
      }
    } catch {
      // Non-blocking fallback
    } finally {
      setEnrolledLoading(false);
    }
  };

  const activeFrame: SweepFrame | undefined = frames[activeFrameIdx];
  const activeResult: DemoAnalysisResponse | null = activeFrame?.result || null;

  // Consolidated multi-frame attendance union
  const consolidated = useMemo(() => {
    const grantedMap = new Map<string, DemoStudentResult>();
    let totalDetections = 0;
    let totalStrangers = 0;

    for (const f of frames) {
      if (!f.result) continue;
      totalDetections += f.result.total_detected_faces;
      totalStrangers += f.result.unknown_count;
      for (const g of f.result.attendance_granted) {
        const prev = grantedMap.get(g.student_id);
        if (!prev || (g.similarity_score ?? 0) > (prev.similarity_score ?? 0)) {
          grantedMap.set(g.student_id, g);
        }
      }
    }

    const grantedList = Array.from(grantedMap.values());
    const grantedIds = new Set(grantedList.map((g) => g.student_id));
    const absentList = enrolledStudents.filter((s) => !grantedIds.has(s.student_id));

    return {
      grantedList,
      absentList,
      totalDetections,
      totalStrangers,
      grantedCount: grantedList.length,
      absentCount: absentList.length,
      totalEnrolled: enrolledStudents.length || (frames[0]?.result?.total_enrolled_students ?? 0),
    };
  }, [frames, enrolledStudents]);

  const handleFilesSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const selectedFiles = Array.from(e.target.files);

    const newFrames: SweepFrame[] = selectedFiles.map((f, i) => ({
      id: `${Date.now()}-${i}-${f.name}`,
      name: `Shot #${frames.length + i + 1}`,
      file: f,
      previewUrl: URL.createObjectURL(f),
      result: null,
      loading: true,
      error: null,
    }));

    const startIndex = frames.length;
    setFrames((prev) => [...prev, ...newFrames]);
    setActiveFrameIdx(startIndex);
    setSelectedFaceIdx(null);

    // Process each new frame sequentially through YuNet & SFace
    for (let i = 0; i < newFrames.length; i++) {
      const frameToRun = newFrames[i];
      try {
        const res = await analyzeDemoPhoto(
          frameToRun.file,
          matchThreshold,
          marginThreshold,
          blurThreshold,
          selectedDepartment
        );
        setFrames((prev) =>
          prev.map((f) => (f.id === frameToRun.id ? { ...f, result: res, loading: false } : f))
        );
      } catch (err: any) {
        setFrames((prev) =>
          prev.map((f) =>
            f.id === frameToRun.id
              ? { ...f, error: err?.message || "Failed to analyze frame", loading: false }
              : f
          )
        );
      }
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const reanalyzeAllFrames = async () => {
    if (frames.length === 0) return;
    setFrames((prev) => prev.map((f) => ({ ...f, loading: true, error: null })));

    for (const f of frames) {
      try {
        const res = await analyzeDemoPhoto(
          f.file,
          matchThreshold,
          marginThreshold,
          blurThreshold,
          selectedDepartment
        );
        setFrames((prev) =>
          prev.map((item) => (item.id === f.id ? { ...item, result: res, loading: false } : item))
        );
      } catch (err: any) {
        setFrames((prev) =>
          prev.map((item) =>
            item.id === f.id
              ? { ...item, error: err?.message || "Inference failed", loading: false }
              : item
          )
        );
      }
    }
  };

  const testStudentPhoto = async (student: DemoEnrolledStudentSummary) => {
    if (!student.photo_url) return;
    try {
      const res = await fetch(student.photo_url);
      const blob = await res.blob();
      const testFile = new File([blob], `${student.roll_number}_ref.jpg`, {
        type: blob.type || "image/jpeg",
      });

      const newFrame: SweepFrame = {
        id: `ref-${student.roll_number}-${Date.now()}`,
        name: `${student.full_name.split(" ")[0]} (Ref)`,
        file: testFile,
        previewUrl: student.photo_url,
        result: null,
        loading: true,
        error: null,
      };

      const newIdx = frames.length;
      setFrames((prev) => [...prev, newFrame]);
      setActiveFrameIdx(newIdx);
      setSelectedFaceIdx(null);

      const analysis = await analyzeDemoPhoto(
        testFile,
        matchThreshold,
        marginThreshold,
        blurThreshold,
        selectedDepartment
      );
      setFrames((prev) =>
        prev.map((f) => (f.id === newFrame.id ? { ...f, result: analysis, loading: false } : f))
      );
    } catch (err: any) {
      // Handled gracefully
    }
  };

  const removeFrame = (frameId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setFrames((prev) => {
      const next = prev.filter((f) => f.id !== frameId);
      if (activeFrameIdx >= next.length) {
        setActiveFrameIdx(Math.max(0, next.length - 1));
      }
      return next;
    });
  };

  const clearAllFrames = () => {
    setFrames([]);
    setActiveFrameIdx(0);
    setSelectedFaceIdx(null);
  };

  const selectedFaceData = useMemo(() => {
    if (!activeResult || selectedFaceIdx === null) return null;
    return activeResult.detected_faces.find((f) => f.face_index === selectedFaceIdx) || null;
  }, [activeResult, selectedFaceIdx]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Hidden Multi-file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*"
        onChange={handleFilesSelected}
        className="hidden"
      />

      {/* Header Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 mb-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Multi-Frame Sweep Sandbox â€¢ PostgreSQL Ground Truth</span>
          </div>
          <h1 className="text-2xl font-serif font-bold text-slate-900 tracking-tight">
            Face Recognition Ground-Truth Inspector & Multi-Photo Sweep
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
            Upload multiple classroom sweep photos taken from different room angles. The system performs YuNet detection,
            128-D SFace embedding extraction, and consolidated multi-frame union matching against active database identities.
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="px-3.5 py-2 rounded-xl text-xs font-medium border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 flex items-center space-x-2 transition shadow-sm"
          >
            <Sliders className="w-3.5 h-3.5 text-slate-500" />
            <span>{showConfig ? "Hide Calibration" : `Calibration (Ï„ = ${matchThreshold.toFixed(3)})`}</span>
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-institutional-navy text-white hover:bg-slate-800 transition flex items-center space-x-2 shadow-sm"
          >
            <Upload className="w-4 h-4" />
            <span>Add Sweep Photos</span>
          </button>
        </div>
      </div>

      {/* Calibration Controls */}
      {showConfig && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4 shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                <span>Cosine Match Threshold (Ï„)</span>
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
                <span>Lookalike Margin (Î”s)</span>
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
              <p className="text-[11px] text-slate-500 mt-1">Minimum difference between top 1 and top 2 candidates.</p>
            </div>
            <div>
              <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                <span>Laplacian Blur Limit</span>
                <span className="font-mono text-slate-700 font-bold">{blurThreshold.toFixed(0)}</span>
              </div>
              <input
                type="range"
                min="10"
                max="60"
                step="5"
                value={blurThreshold}
                onChange={(e) => setBlurThreshold(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-slate-700"
              />
              <p className="text-[11px] text-slate-500 mt-1">20 is optimal for classroom back-row faces.</p>
            </div>
          </div>
          <div className="flex justify-end pt-2 border-t border-slate-200">
            <button
              onClick={reanalyzeAllFrames}
              className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-100 transition shadow-xs flex items-center space-x-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Apply & Re-run Sweep Calibration</span>
            </button>
          </div>
        </div>
      )}

      {/* Multi-Photo Filmstrip Bar (When frames exist) */}
      {frames.length > 0 && (
        <div className="bg-white p-3.5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between gap-3 overflow-x-auto">
          <div className="flex items-center space-x-2 shrink-0">
            <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5 mr-2">
              <Layers className="w-4 h-4 text-institutional-navy" />
              <span>Sweep Shots ({frames.length})</span>
            </span>

            {frames.map((frame, idx) => {
              const isActive = idx === activeFrameIdx;
              const granted = frame.result?.attendance_granted.length ?? 0;
              const detected = frame.result?.total_detected_faces ?? 0;

              return (
                <div
                  key={frame.id}
                  onClick={() => {
                    setActiveFrameIdx(idx);
                    setSelectedFaceIdx(null);
                  }}
                  className={`relative flex items-center space-x-2 px-3 py-1.5 rounded-xl border cursor-pointer transition shadow-xs select-none ${
                    isActive
                      ? "bg-institutional-navy text-white border-institutional-navy ring-2 ring-institutional-navy/20"
                      : "bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200"
                  }`}
                >
                  <img
                    src={frame.previewUrl}
                    alt={frame.name}
                    className="w-7 h-7 rounded-md object-cover border border-white/30 shrink-0"
                  />
                  <div className="text-left">
                    <p className="text-xs font-bold leading-tight truncate max-w-[100px]">{frame.name}</p>
                    <p className={`text-[10px] ${isActive ? "text-slate-200" : "text-slate-500"}`}>
                      {frame.loading ? "Analyzing..." : `${detected} faces (${granted} granted)`}
                    </p>
                  </div>
                  {frames.length > 1 && (
                    <button
                      type="button"
                      onClick={(e) => removeFrame(frame.id, e)}
                      className={`ml-1 p-0.5 rounded hover:bg-white/20 transition ${
                        isActive ? "text-white" : "text-slate-400 hover:text-slate-600"
                      }`}
                      title="Remove shot"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-3 py-1.5 rounded-xl border border-dashed border-slate-300 hover:border-institutional-navy text-xs font-semibold text-slate-700 hover:text-institutional-navy bg-slate-50 transition flex items-center space-x-1"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Angle</span>
            </button>
            <button
              onClick={clearAllFrames}
              className="px-2.5 py-1.5 rounded-xl text-xs font-medium text-slate-500 hover:text-red-600 hover:bg-red-50 transition"
              title="Clear all shots"
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {/* Consolidated Attendance Banner */}
      {frames.length > 0 && (
        <div className="bg-linear-to-r from-emerald-50 via-teal-50 to-slate-50 p-4 rounded-2xl border border-emerald-200 shadow-xs flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-bold text-sm shadow-xs">
              <Check className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-semibold text-emerald-900 uppercase tracking-wider">
                Multi-Frame Sweep Union Attendance
              </p>
              <p className="text-base font-bold text-slate-900 font-serif">
                {consolidated.grantedCount} / {consolidated.totalEnrolled} Students Present (
                {consolidated.totalEnrolled > 0
                  ? ((consolidated.grantedCount / consolidated.totalEnrolled) * 100).toFixed(1)
                  : "0.0"}
                %)
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-xs">
            <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 font-semibold border border-emerald-300">
              {consolidated.grantedCount} Verified Present
            </span>
            <span className="px-3 py-1 rounded-full bg-amber-100 text-amber-800 font-semibold border border-amber-300">
              {consolidated.absentCount} Absent
            </span>
            <span className="px-3 py-1 rounded-full bg-slate-100 text-slate-700 font-medium border border-slate-300">
              Across {frames.length} Frame{frames.length === 1 ? "" : "s"}
            </span>
          </div>
        </div>
      )}

      {/* Main Grid: Photo Visualizer vs Evidence Ledger */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Augmented Photo Canvas */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-100">
            <h2 className="text-sm font-semibold text-slate-800 flex items-center space-x-2">
              <Camera className="w-4 h-4 text-slate-500" />
              <span>
                {activeFrame ? `${activeFrame.name} (Visual Ground Truth)` : "Photo Canvas"}
              </span>
            </h2>

            {/* Display Mode Toggle (Pills | Boxes Only | Raw Photo) */}
            {activeFrame && (
              <div className="flex items-center space-x-1.5">
                <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-0.5 shadow-xs text-xs font-medium">
                  <button
                    type="button"
                    onClick={() => setOverlayMode("clean")}
                    className={`px-2 py-1 rounded-md transition ${
                      overlayMode === "clean"
                        ? "bg-white text-institutional-navy font-bold shadow-xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                    title="Clean compact pills on matches, tiny dot on strangers, no text clutter"
                  >
                    Clean Pills
                  </button>
                  <button
                    type="button"
                    onClick={() => setOverlayMode("boxesOnly")}
                    className={`px-2 py-1 rounded-md transition ${
                      overlayMode === "boxesOnly"
                        ? "bg-white text-institutional-navy font-bold shadow-xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                    title="100% visible faces: boxes only, zero text banners"
                  >
                    Boxes Only
                  </button>
                  <button
                    type="button"
                    onClick={() => setOverlayMode("rawPhoto")}
                    className={`px-2 py-1 rounded-md transition ${
                      overlayMode === "rawPhoto"
                        ? "bg-white text-institutional-navy font-bold shadow-xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                    title="Pristine original photo with no overlays"
                  >
                    Raw Photo
                  </button>
                </div>

                {/* Zoom Controls */}
                <div className="flex items-center space-x-1 border-l border-slate-200 pl-2">
                  <button
                    type="button"
                    onClick={() => setZoomLevel((z) => Math.max(1.0, z - 0.25))}
                    disabled={zoomLevel <= 1.0}
                    className="p-1 rounded hover:bg-slate-100 text-slate-500 disabled:opacity-40"
                    title="Zoom Out"
                  >
                    <ZoomOut className="w-3.5 h-3.5" />
                  </button>
                  <span className="text-[10px] font-mono font-semibold text-slate-600 min-w-[28px] text-center">
                    {Math.round(zoomLevel * 100)}%
                  </span>
                  <button
                    type="button"
                    onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.25))}
                    disabled={zoomLevel >= 2.5}
                    className="p-1 rounded hover:bg-slate-100 text-slate-500 disabled:opacity-40"
                    title="Zoom In"
                  >
                    <ZoomIn className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {activeFrame ? (
            <div className="relative rounded-xl overflow-hidden bg-slate-900 flex items-center justify-center min-h-[380px] max-h-[560px]">
              <div
                className="relative inline-block max-h-[560px] transition-transform duration-200"
                style={{ transform: `scale(${zoomLevel})`, transformOrigin: "center center" }}
              >
                <img
                  src={activeFrame.previewUrl}
                  alt={activeFrame.name}
                  className="max-h-[560px] w-auto object-contain select-none block"
                />

                {/* SVG Bounding Boxes Overlay (Hidden in rawPhoto mode) */}
                {overlayMode !== "rawPhoto" && activeResult && (
                  <svg
                    className="absolute inset-0 w-full h-full pointer-events-none"
                    viewBox="0 0 100 100"
                    preserveAspectRatio="none"
                  >
                    {activeResult.detected_faces.map((face: DemoFaceBox) => {
                      const [x1, y1, x2, y2] = face.box;
                      const isSelected = selectedFaceIdx === face.face_index;
                      const isMatched = face.status === "MATCHED";

                      return (
                        <g
                          key={face.face_index}
                          className="pointer-events-auto cursor-pointer"
                          onClick={() => setSelectedFaceIdx(face.face_index)}
                        >
                          {/* Main Bounding Box */}
                          <rect
                            x={`${x1 * 100}%`}
                            y={`${y1 * 100}%`}
                            width={`${(x2 - x1) * 100}%`}
                            height={`${(y2 - y1) * 100}%`}
                            fill="none"
                            stroke={isSelected ? "#38BDF8" : face.color_hex}
                            strokeWidth={isSelected ? "1.4" : "0.6"}
                            strokeDasharray={face.quality_reason !== "QUALITY_ACCEPTABLE" ? "1, 1" : "none"}
                            rx="0.8"
                          />

                          {/* Selected Face Glowing Border */}
                          {isSelected && (
                            <rect
                              x={`${x1 * 100 - 0.4}%`}
                              y={`${y1 * 100 - 0.4}%`}
                              width={`${(x2 - x1) * 100 + 0.8}%`}
                              height={`${(y2 - y1) * 100 + 0.8}%`}
                              fill="none"
                              stroke="#FFFFFF"
                              strokeWidth="0.4"
                              rx="1.2"
                            />
                          )}
                        </g>
                      );
                    })}
                  </svg>
                )}

                {/* Overlays in Clean Mode: Compact First-Name Pills for Matches, Tiny Dot for Strangers */}
                {overlayMode === "clean" &&
                  activeResult &&
                  activeResult.detected_faces.map((face: DemoFaceBox) => {
                    const [x1, y1] = face.box;
                    const isSelected = selectedFaceIdx === face.face_index;
                    const isMatched = face.status === "MATCHED";

                    if (isMatched) {
                      const firstName = face.full_name ? face.full_name.split(" ")[0] : "Student";
                      return (
                        <div
                          key={`clean-badge-${face.face_index}`}
                          onClick={() => setSelectedFaceIdx(face.face_index)}
                          style={{
                            left: `${x1 * 100}%`,
                            top: `${Math.max(1, y1 * 100 - 3.5)}%`,
                          }}
                          className={`absolute transform -translate-y-full px-1.5 py-0.5 rounded-md text-[10px] font-bold text-white shadow-md cursor-pointer whitespace-nowrap z-10 transition-transform hover:scale-110 flex items-center space-x-1 ${
                            isSelected ? "bg-sky-600 ring-2 ring-white" : "bg-emerald-600"
                          }`}
                        >
                          <Check className="w-2.5 h-2.5" />
                          <span>
                            {firstName} ({face.similarity_score?.toFixed(2)})
                          </span>
                        </div>
                      );
                    }

                    // For strangers/rejected: Tiny 16px indicator dot at top-left corner (NO giant banners)
                    return (
                      <div
                        key={`clean-dot-${face.face_index}`}
                        onClick={() => setSelectedFaceIdx(face.face_index)}
                        style={{
                          left: `${x1 * 100}%`,
                          top: `${y1 * 100}%`,
                        }}
                        className={`absolute -translate-x-1/2 -translate-y-1/2 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold text-white shadow-sm cursor-pointer z-10 transition-transform hover:scale-125 ${
                          isSelected ? "bg-sky-500 ring-2 ring-white" : "bg-red-500"
                        }`}
                        title={face.badge_label}
                      >
                        ?
                      </div>
                    );
                  })}
              </div>

              {activeFrame.loading && (
                <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-xs flex flex-col items-center justify-center text-white space-y-3 z-20">
                  <RefreshCw className="w-8 h-8 animate-spin text-emerald-400" />
                  <p className="text-sm font-semibold">Running YuNet Detection & SFace Extraction...</p>
                  <p className="text-xs text-slate-300">Matching against enrolled database identities</p>
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
                Click here or use the button above to upload single or multiple classroom sweep photos.
              </p>
              <div className="mt-4 inline-flex items-center space-x-1.5 px-3 py-1 bg-white border border-slate-200 rounded-full text-xs font-medium text-slate-600 shadow-xs">
                <Users className="w-3.5 h-3.5 text-emerald-600" />
                <span>Active Gallery: {enrolledStudents.length} Real Students Registered</span>
              </div>
            </div>
          )}

          {/* Color Legend & Inspection Drawer */}
          <div className="space-y-3 pt-2 border-t border-slate-100">
            {/* Selected Face Inspection Drawer */}
            {selectedFaceData && (
              <div className="p-3 bg-sky-50/80 border border-sky-200 rounded-xl flex items-center justify-between gap-4">
                <div className="flex items-center space-x-3">
                  <img
                    src={selectedFaceData.face_crop_base64}
                    alt={`Face ${selectedFaceData.face_index}`}
                    className="w-12 h-12 rounded-lg object-cover border border-sky-300"
                  />
                  <div>
                    <div className="flex items-center space-x-1.5">
                      <span className="text-xs font-bold text-sky-950">
                        Face #{selectedFaceData.face_index}:{" "}
                        {selectedFaceData.full_name || "Unidentified Visitor"}
                      </span>
                      {selectedFaceData.status === "MATCHED" && (
                        <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-100 text-emerald-800">
                          PRESENT
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-sky-700 font-mono">
                      {selectedFaceData.roll_number
                        ? `Roll: ${selectedFaceData.roll_number} • Sim: ${selectedFaceData.similarity_score?.toFixed(3)}`
                        : `Status: ${selectedFaceData.status} (Sim: ${selectedFaceData.similarity_score?.toFixed(3) || "0.000"})`}
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setSelectedFaceIdx(null)}
                  className="text-xs text-sky-700 hover:text-sky-900 font-medium px-2 py-1 rounded hover:bg-sky-100 transition"
                >
                  Close
                </button>
              </div>
            )}

            <div className="flex flex-wrap items-center gap-3 text-xs">
              <span className="inline-flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <span className="text-slate-700 font-medium">Matched (Present)</span>
              </span>
              <span className="inline-flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                <span className="text-slate-700 font-medium">Lookalike Ambiguous</span>
              </span>
              <span className="inline-flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
                <span className="text-slate-700 font-medium">Unregistered Visitor</span>
              </span>
              <span className="inline-flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
                <span className="text-slate-700 font-medium">Low Texture Blur</span>
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Ground-Truth Evidence Ledger */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col h-[640px]">
          {/* Summary Tabs */}
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
              <span>
                Granted ({frames.length > 1 ? consolidated.grantedCount : (activeResult?.present_count ?? 0)})
              </span>
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
              <span>
                Absent ({frames.length > 1 ? consolidated.absentCount : (activeResult?.absent_count ?? 0)})
              </span>
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
              <span>
                Strangers ({activeResult?.unknown_count ?? 0})
              </span>
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {activeFrame?.error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-start space-x-2">
                <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                <span>{activeFrame.error}</span>
              </div>
            )}

            {!activeResult && !activeFrame?.loading && (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 p-6">
                <Eye className="w-8 h-8 text-slate-300 mb-2" />
                <p className="text-xs">Select or capture a photo to view face-by-face biometric verification.</p>
              </div>
            )}

            {/* TAB 1: ATTENDANCE GRANTED (Split-Screen Evidence) */}
            {activeTab === "granted" && activeResult && (
              <>
                {activeResult.attendance_granted.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-10">No enrolled students spotted in this photo.</p>
                ) : (
                  activeResult.attendance_granted.map((item: DemoStudentResult) => (
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
                          <span className="text-[9px] text-slate-500 font-medium mt-1">Classroom Crop</span>
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
            {activeTab === "absent" && activeResult && (
              <>
                {activeResult.attendance_not_granted.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-10">All enrolled students are present!</p>
                ) : (
                  activeResult.attendance_not_granted.map((item: DemoStudentResult) => (
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
            {activeTab === "strangers" && activeResult && (
              <>
                {activeResult.unidentified_faces.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-10">Zero unknown or rejected faces in photograph.</p>
                ) : (
                  activeResult.unidentified_faces.map((face: DemoFaceBox) => (
                    <div
                      key={`unknown-${face.face_index}`}
                      onClick={() => setSelectedFaceIdx(face.face_index)}
                      className={`p-3 rounded-xl border transition cursor-pointer space-y-2 ${
                        selectedFaceIdx === face.face_index
                          ? "border-sky-400 bg-sky-50/50"
                          : "border-red-200 bg-red-50/30 hover:bg-red-50/60"
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <img
                          src={face.face_crop_base64}
                          alt="Unknown crop"
                          className="w-11 h-11 rounded-md object-cover border border-red-200 shrink-0"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-red-900 truncate">
                              Face #{face.face_index} â€” {face.status}
                            </span>
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-red-100 text-red-700 shrink-0">
                              REJECTED
                            </span>
                          </div>
                          <p className="text-[10px] text-slate-600 mt-0.5 truncate">{face.badge_label}</p>
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

      {/* Database Biometric Gallery (Authoritative Database Profiles) */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-100">
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-emerald-600" />
            <h2 className="text-base font-serif font-bold text-slate-900">
              Enrolled Database Biometric Gallery
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              {enrolledStudents.length} Registered Identities
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={selectedDepartment}
              onChange={(e) => setSelectedDepartment(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-slate-50 text-slate-700 font-medium focus:outline-none focus:ring-1 focus:ring-institutional-navy"
            >
              <option value="ALL">All Departments (Universal)</option>
              <option value="CSD">CSD (Data Science)</option>
              <option value="CSE">CSE (Computer Science)</option>
              <option value="ECE">ECE (Electronics)</option>
              <option value="MECH">MECH (Mechanical)</option>
              <option value="EEE">EEE (Electrical)</option>
              <option value="CIVIL">CIVIL</option>
              <option value="IT">IT</option>
            </select>

            <button
              onClick={() => loadEnrolledGallery(selectedDepartment)}
              disabled={enrolledLoading}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 transition shadow-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-slate-500 ${enrolledLoading ? "animate-spin" : ""}`} />
              <span>Refresh Gallery</span>
            </button>
            <Link
              href="/admin/enrollment"
              className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-institutional-navy hover:text-institutional-blue transition"
            >
              <span>Manage Biometric Queue</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {enrolledLoading ? (
          <div className="py-12 text-center text-slate-500 text-xs flex flex-col items-center justify-center space-y-2">
            <RefreshCw className="w-5 h-5 animate-spin text-institutional-navy" />
            <span>Loading database biometric templates...</span>
          </div>
        ) : enrolledStudents.length === 0 ? (
          <div className="py-10 text-center text-slate-500 text-xs">
            <p>No active enrolled students found in database.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {enrolledStudents.map((student) => (
              <div
                key={student.student_id}
                className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 hover:border-emerald-300 transition-all shadow-xs flex flex-col justify-between space-y-3"
              >
                <div className="flex items-start space-x-3">
                  <div className="relative shrink-0">
                    {student.photo_url ? (
                      <img
                        src={student.photo_url}
                        alt={student.full_name}
                        className="w-14 h-14 rounded-xl object-cover border border-slate-200 shadow-xs"
                      />
                    ) : (
                      <div className="w-14 h-14 rounded-xl bg-slate-200 flex items-center justify-center text-slate-600 font-bold text-sm">
                        {student.full_name.slice(0, 2).toUpperCase()}
                      </div>
                    )}
                    <span
                      className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-emerald-500 border-2 border-white"
                      title="128-D Biometric Vector Active"
                    />
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-bold text-slate-900 truncate" title={student.full_name}>
                      {student.full_name}
                    </p>
                    <p className="text-[11px] font-mono font-semibold text-institutional-navy">
                      {student.roll_number}
                    </p>
                    <span className="inline-flex items-center space-x-1 mt-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                      <Sparkles className="w-2.5 h-2.5" />
                      <span>128-D SFace Enrolled</span>
                    </span>
                  </div>
                </div>

                {student.photo_url && (
                  <button
                    type="button"
                    onClick={() => testStudentPhoto(student)}
                    className="w-full py-1.5 px-2 bg-white hover:bg-institutional-navy hover:text-white text-slate-700 border border-slate-200 rounded-lg text-xs font-semibold transition-colors flex items-center justify-center space-x-1.5 shadow-xs"
                  >
                    <Camera className="w-3.5 h-3.5" />
                    <span>Test Match In Visualizer</span>
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
