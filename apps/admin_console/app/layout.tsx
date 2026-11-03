import React from "react";
import type { Metadata } from "next";
import "./globals.css";
import { AdminSidebar } from "@/components/sidebar";
import { AdminHeader } from "@/components/header";

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
          <AdminHeader />

          {/* Main Workspace Surface */}
          <main id="main-content" tabIndex={-1} className="flex-1 p-8 outline-hidden">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

