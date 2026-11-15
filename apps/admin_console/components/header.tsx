"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/theme-toggle";

export function AdminHeader() {
  const pathname = usePathname();

  if (pathname === "/login" || pathname === "/admin/login" || pathname === "/enroll" || pathname === "/enrollment") {
    return null;
  }

  return (
    <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-8 flex items-center justify-between sticky top-0 z-10 transition-colors">
      <div className="flex items-center space-x-3">
        <span className="text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
          Institutional Portal
        </span>
        <span className="text-sm font-medium text-slate-500 dark:text-slate-400">
          Kakatiya University College of Engineering & Technology
        </span>
      </div>
      <div className="flex items-center space-x-4">
        <ThemeToggle />
        <div className="flex items-center space-x-2 text-xs font-medium text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 px-2.5 py-1 rounded-full">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Postgres Ledger Authoritative</span>
        </div>
        <div className="text-sm text-slate-700 dark:text-slate-200 font-medium">
          Admin Console
        </div>
      </div>
    </header>
  );
}
