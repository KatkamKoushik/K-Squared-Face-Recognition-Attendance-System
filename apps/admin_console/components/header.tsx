"use client";

import React from "react";
import { usePathname } from "next/navigation";

export function AdminHeader() {
  const pathname = usePathname();

  if (pathname === "/login" || pathname === "/admin/login" || pathname === "/enroll" || pathname === "/enrollment") {
    return null;
  }

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-10">
      <div className="flex items-center space-x-3">
        <span className="text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-600">
          Institutional Portal
        </span>
        <span className="text-sm font-medium text-slate-500">
          Kakatiya University College of Engineering & Technology
        </span>
      </div>
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Postgres Ledger Authoritative</span>
        </div>
        <div className="text-sm text-slate-700 font-medium">
          Admin Console
        </div>
      </div>
    </header>
  );
}
