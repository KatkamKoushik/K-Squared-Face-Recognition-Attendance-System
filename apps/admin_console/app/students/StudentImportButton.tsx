"use client";

import React, { useRef, useState } from "react";
import { UploadCloud, CheckCircle2 } from "lucide-react";
import { importStudentsCsv } from "@/lib/api";

export default function StudentImportButton() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    try {
      const res = await importStudentsCsv(file);
      alert(`Import completed: ${res.imported_count} students registered, ${res.skipped_count} skipped.`);
      window.location.reload();
    } catch (err: any) {
      alert("CSV Import failed: " + err.message);
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="inline-flex items-center space-x-2">
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={handleFileChange}
      />
      <button
        type="button"
        disabled={importing}
        onClick={() => fileInputRef.current?.click()}
        className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 transition-colors shadow-xs disabled:opacity-50"
      >
        <UploadCloud className="w-4 h-4 text-slate-500" />
        <span>{importing ? "Importing CSV..." : "Bulk Import CSV"}</span>
      </button>
    </div>
  );
}
