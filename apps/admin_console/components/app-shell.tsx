"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { AdminSidebar } from "@/components/sidebar";
import { AdminHeader } from "@/components/header";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isPublicRoute =
    pathname === "/login" ||
    pathname === "/admin/login" ||
    pathname === "/enroll" ||
    pathname === "/enrollment";

  if (isPublicRoute) {
    return (
      <div className="w-full min-h-screen bg-slate-50">
        <main id="main-content" tabIndex={-1} className="outline-hidden">
          {children}
        </main>
      </div>
    );
  }

  return (
    <div className="flex w-full min-h-screen bg-slate-50">
      <AdminSidebar />
      <div className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
        <AdminHeader />
        <main id="main-content" tabIndex={-1} className="flex-1 p-8 outline-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}
