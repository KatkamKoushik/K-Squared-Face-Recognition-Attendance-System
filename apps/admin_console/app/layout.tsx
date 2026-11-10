import React from "react";
import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/app-shell";

export const metadata: Metadata = {
  title: "FRS V7.1 K² — Attendance Portal & Admin Console",
  description: "Academic Biometric Enrollment and Attendance Ledger for KUCE&T",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 antialiased">
        {/* Accessible Skip to Content Link (Checklist Section 38) */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-institutional-navy focus:text-white focus:rounded-md focus:shadow-lg focus:outline-hidden"
        >
          Skip to main content
        </a>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
