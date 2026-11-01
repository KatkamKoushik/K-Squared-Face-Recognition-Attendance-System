import React from "react";
import type { Metadata } from "next";
import "./globals.css";
import { AdminSidebar } from "@/components/sidebar";

export const metadata: Metadata = {
  title: "FRS V7.1 K² — Admin Console",
  description: "Academic Administration and Attendance Ledger for KUCET",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 antialiased flex">
        {/* Accessible Skip to Content Link (Checklist Section 38) */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-institutional-navy focus:text-white focus:rounded-md focus:shadow-lg focus:outline-hidden"
        >
          Skip to main content
        </a>
        <AdminSidebar />
        <div className="flex-1 flex flex-col min-h-screen overflow-x-hidden">
          {/* Top Header */}
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

          {/* Main Workspace Surface */}
          <main id="main-content" tabIndex={-1} className="flex-1 p-8 outline-hidden">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

