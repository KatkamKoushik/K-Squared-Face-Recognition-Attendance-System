"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { GraduationCap, ShieldCheck, ArrowRight, AlertCircle } from "lucide-react";
import { login, setAuthToken, setStoredUser } from "@/lib/api";

export default function StudentLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await login(email, password);
      if (!res) {
        throw new Error("Invalid institutional credentials. Please try again.");
      }
      setAuthToken(res.access_token);
      setStoredUser({
        user_id: res.user_id,
        email: res.email,
        role: res.role,
      });

      router.push("/student");
    } catch (err: any) {
      setError(err?.message || "Authentication failed. Check your student email and password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="w-14 h-14 bg-institutional-navy rounded-2xl flex items-center justify-center mx-auto shadow-md">
          <GraduationCap className="w-8 h-8 text-amber-400" />
        </div>
        <h2 className="mt-4 text-2xl font-serif font-bold text-institutional-navy">
          KUCET Student Attendance Portal
        </h2>
        <p className="mt-1 text-sm text-institutional-muted">
          KU College of Engineering & Technology, Warangal
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-sm border border-slate-200 rounded-2xl sm:px-10">
          {error && (
            <div className="mb-6 p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start space-x-3 text-rose-800 text-sm">
              <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
              <div>{error}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                Institutional Email or Roll Number
              </label>
              <input
                type="text"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="student@kucet.ac.in"
                className="mt-1.5 block w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm shadow-xs focus:ring-2 focus:ring-institutional-navy focus:border-institutional-navy"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your student password"
                className="mt-1.5 block w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm shadow-xs focus:ring-2 focus:ring-institutional-navy focus:border-institutional-navy"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg bg-institutional-navy text-white text-sm font-semibold hover:bg-institutional-navy/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-institutional-navy shadow-sm transition-colors disabled:opacity-50"
            >
              <span>{loading ? "Authenticating..." : "Sign In to Student Portal"}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-100 text-center space-y-3">
            <Link
              href="/enroll"
              className="text-xs text-institutional-blue hover:underline block font-medium"
            >
              Need to submit biometric photo? Register for attendance enrollment &rarr;
            </Link>
            <Link
              href="/login"
              className="text-xs text-slate-500 hover:underline block"
            >
              Are you a faculty or administrator? Faculty Login &rarr;
            </Link>
          </div>
        </div>

        <div className="mt-6 text-center text-xs text-slate-500 flex items-center justify-center space-x-1.5">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Institutional attendance data is cryptographically audited and ACID-guaranteed.</span>
        </div>
      </div>
    </div>
  );
}
