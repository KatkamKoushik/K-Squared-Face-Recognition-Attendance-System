"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Building2,
  Users,
  BookOpen,
  GitMerge,
  Eye,
  BarChart3,
  FileCheck2,
  Activity,
  LogOut,
  ShieldAlert,
  ShieldCheck,
  FlaskConical,
  LogIn,
  FileText,
  Camera,
} from "lucide-react";
import { logout, getStoredUser, StoredAuthUser } from "@/lib/api";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  allowedRoles?: string[];
}

const allNavigationItems: NavItem[] = [
  { name: "Executive Overview", href: "/", icon: LayoutDashboard, allowedRoles: ["DEVELOPER", "SUPER_ADMIN", "ADMIN"] },
  { name: "Demo Visualizer", href: "/demo", icon: Camera, allowedRoles: ["DEVELOPER", "SUPER_ADMIN", "ADMIN", "SUB_ADMIN", "FACULTY"] },
  { name: "Biometric Queue", href: "/admin/enrollment", icon: ShieldAlert, allowedRoles: ["DEVELOPER", "SUPER_ADMIN", "ADMIN"] },
  { name: "Attendance Appeals", href: "/admin/appeals", icon: FileText, allowedRoles: ["DEVELOPER", "SUPER_ADMIN", "ADMIN"] },
  { name: "Academic Structure", href: "/academic/structure", icon: Building2, allowedRoles: ["DEVELOPER", "SUPER_ADMIN"] },
  { name: "Student Enrolment", href: "/students", icon: Users, allowedRoles: ["DEVELOPER", "SUPER_ADMIN", "ADMIN"] },
  { name: "Course Offerings", href: "/academic/offerings", icon: BookOpen, allowedRoles: ["DEVELOPER", "SUPER_ADMIN", "ADMIN", "SUB_ADMIN", "FACULTY"] },
  { name: "Joint-Class Groups", href: "/academic/joint-groups", icon: GitMerge, allowedRoles: ["DEVELOPER", "SUPER_ADMIN", "ADMIN"] },
  { name: "Live Roster Preview", href: "/roster-preview", icon: Eye, allowedRoles: ["DEVELOPER", "SUPER_ADMIN", "ADMIN", "SUB_ADMIN", "FACULTY"] },
  { name: "Attendance Analytics", href: "/reports/attendance", icon: BarChart3, allowedRoles: ["DEVELOPER", "SUPER_ADMIN", "ADMIN", "SUB_ADMIN", "FACULTY"] },
  { name: "Governance & Privacy", href: "/governance", icon: ShieldCheck, allowedRoles: ["DEVELOPER", "SUPER_ADMIN"] },
  { name: "Controlled Pilot", href: "/pilot", icon: FlaskConical, allowedRoles: ["DEVELOPER", "SUPER_ADMIN"] },
  { name: "Audit Trail Browser", href: "/audit/logs", icon: FileCheck2, allowedRoles: ["DEVELOPER", "SUPER_ADMIN"] },
  { name: "System Readiness", href: "/system/readiness", icon: Activity, allowedRoles: ["DEVELOPER"] },
  { name: "Student Portal", href: "/student/login", icon: LogIn },
];

function getRoleDisplay(user: StoredAuthUser | null) {
  if (!user) return { title: "Role: Academic Administrator", subtitle: "Public Institutional Preview" };
  switch (user.role) {
    case "DEVELOPER":
      return { title: "Tier 1: Developer", subtitle: "System Root & Diagnostics" };
    case "SUPER_ADMIN":
      return { title: "Tier 2: Super Admin", subtitle: "Institutional Authority" };
    case "ADMIN":
      return { title: "Tier 3: Department Admin", subtitle: user.department_id ? "Department Scoped" : "Department Head" };
    case "SUB_ADMIN":
    case "FACULTY":
      return { title: "Tier 4: Sub-Admin (Faculty)", subtitle: "Teaching Class Scope" };
    case "STUDENT":
      return { title: "Tier 5: Student", subtitle: "Self-Service Identity" };
    default:
      return { title: `Role: ${user.role}`, subtitle: user.email };
  }
}

export function AdminSidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<StoredAuthUser | null>(null);

  useEffect(() => {
    setUser(getStoredUser());
  }, [pathname]);

  if (
    pathname === "/login" ||
    pathname === "/admin/login" ||
    pathname === "/enroll" ||
    pathname === "/enrollment" ||
    pathname === "/student/login" ||
    pathname.startsWith("/student")
  ) {
    return null;
  }

  const handleSignOut = () => {
    logout();
    setUser(null);
    router.push("/enroll");
  };

  const navItems = user
    ? allNavigationItems.filter(
        (item) => !item.allowedRoles || item.allowedRoles.includes(user.role)
      )
    : allNavigationItems;

  const roleInfo = getRoleDisplay(user);

  return (
    <aside className="w-64 bg-institutional-navy text-white flex flex-col min-h-screen border-r border-institutional-navy/20 shrink-0">
      {/* Brand Header */}
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-institutional-blue flex items-center justify-center font-serif font-bold text-lg">
            K²
          </div>
          <div>
            <h1 className="font-serif font-semibold text-lg leading-tight tracking-wide">
              FRS Admin
            </h1>
            <p className="text-xs text-white/60">KUCET Campus Baseline</p>
          </div>
        </div>
      </div>

      {/* Role Badge */}
      <div className="px-6 py-3 bg-white/5 border-b border-white/10 flex items-center space-x-2">
        <ShieldAlert className="w-4 h-4 text-institutional-gold shrink-0" />
        <div className="overflow-hidden">
          <span className="text-xs font-semibold text-white/90 block truncate">
            {roleInfo.title}
          </span>
          <span className="text-[10px] text-white/50 block truncate">
            {user ? `${user.email} (${roleInfo.subtitle})` : roleInfo.subtitle}
          </span>
        </div>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 px-4 py-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-white/15 text-white shadow-2xs font-semibold"
                  : "text-white/80 hover:text-white hover:bg-white/10"
              }`}
            >
              <Icon className="w-4 h-4 text-white/70" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer Info & Sign-out */}
      <div className="p-4 border-t border-white/10">
        <div className="text-xs text-white/50 mb-3 px-2">
          Institutional Release • Spec Ready
        </div>
        {user ? (
          <button
            type="button"
            onClick={handleSignOut}
            className="w-full flex items-center space-x-2 px-3 py-2 rounded-lg text-sm text-red-200 hover:bg-red-500/20 transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        ) : (
          <Link
            href="/login"
            className="w-full flex items-center space-x-2 px-3 py-2 rounded-lg text-sm text-institutional-gold hover:bg-white/10 transition-colors"
          >
            <LogIn className="w-4 h-4" />
            <span>Sign In</span>
          </Link>
        )}
      </div>
    </aside>
  );
}


