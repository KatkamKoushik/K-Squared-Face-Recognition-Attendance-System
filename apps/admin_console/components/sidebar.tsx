import React from "react";
import Link from "next/link";
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
} from "lucide-react";

const navigationItems = [
  { name: "Executive Overview", href: "/", icon: LayoutDashboard },
  { name: "Academic Structure", href: "/academic/structure", icon: Building2 },
  { name: "Student Enrolment", href: "/students", icon: Users },
  { name: "Course Offerings", href: "/academic/offerings", icon: BookOpen },
  { name: "Joint-Class Groups", href: "/academic/joint-groups", icon: GitMerge },
  { name: "Live Roster Preview", href: "/roster-preview", icon: Eye },
  { name: "Attendance Analytics", href: "/reports/attendance", icon: BarChart3 },
  { name: "Audit Trail Browser", href: "/audit/logs", icon: FileCheck2 },
  { name: "System Readiness", href: "/system/readiness", icon: Activity },
];

export function AdminSidebar() {
  return (
    <aside className="w-64 bg-institutional-navy text-white flex flex-col min-h-screen border-r border-institutional-navy/20">
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
        <ShieldAlert className="w-4 h-4 text-institutional-gold" />
        <span className="text-xs font-medium text-white/80">
          Role: Academic Administrator
        </span>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 px-4 py-4 space-y-1">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className="flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium text-white/80 hover:text-white hover:bg-white/10 transition-colors"
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
          Blueprint V7.1 • Spec Ready
        </div>
        <button
          type="button"
          className="w-full flex items-center space-x-2 px-3 py-2 rounded-lg text-sm text-red-200 hover:bg-red-500/20 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}

