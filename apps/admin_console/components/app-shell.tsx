"use client";

import React, { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AdminSidebar } from "@/components/sidebar";
import { AdminHeader } from "@/components/header";
import { getStoredUser } from "@/lib/api";
import { getStoredAdminToken } from "@/lib/session";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [isAuth, setIsAuth] = useState<boolean | null>(null);

  const isPublicRoute =
    pathname === "/login" ||
    pathname === "/admin/login" ||
    pathname === "/enroll" ||
    pathname === "/enrollment" ||
    pathname === "/student/login" ||
    pathname.startsWith("/student");

  useEffect(() => {
    const user = getStoredUser();
    const token = getStoredAdminToken();
    const authed = !!(user || token);
    setIsAuth(authed);

    // If an unauthenticated visitor visits the root or any protected administrative route, redirect to /enroll
    if (!authed && !isPublicRoute) {
      router.replace("/enroll");
    }
  }, [pathname, isPublicRoute, router]);

  // Public views (Enrollment, Login, Student Portal): render clean page without administrative shell
  if (isPublicRoute) {
    return (
      <div className="w-full min-h-screen bg-slate-50">
        <main id="main-content" tabIndex={-1} className="outline-hidden">
          {children}
        </main>
      </div>
    );
  }

  // If unauthenticated on a protected route, show a minimal transition state while routing to /enroll
  if (!isAuth) {
    return (
      <div className="w-full min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-3 border-institutional-navy border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-500 font-medium">Redirecting to Student Enrollment Portal...</p>
        </div>
      </div>
    );
  }

  // Authenticated Administrative View ("Total"): render full sidebar, header, and dashboard features
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
