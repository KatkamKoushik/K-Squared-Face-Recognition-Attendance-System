"use client";

import React, { useEffect } from "react";
import { AlertOctagon, RotateCcw, Home } from "lucide-react";
import Link from "next/link";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log exception to institutional monitoring surface
    console.error("Admin Console Rendering Exception:", error);
  }, [error]);

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="min-h-[60vh] flex items-center justify-center p-6"
    >
      <div className="max-w-lg w-full bg-white rounded-2xl border border-rose-200 shadow-md p-8 text-center space-y-5">
        <div className="w-14 h-14 mx-auto rounded-full bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600">
          <AlertOctagon className="w-8 h-8" />
        </div>

        <div>
          <h2 className="font-serif text-2xl font-bold text-institutional-navy">
            Application Surface Error
          </h2>
          <p className="text-sm text-institutional-muted mt-2">
            An unexpected client rendering failure occurred within this console module.
            Your academic session data remains safely persisted.
          </p>
        </div>

        {error.digest && (
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs font-mono text-slate-600 select-all">
            Digest: {error.digest}
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <button
            type="button"
            onClick={() => reset()}
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-5 py-2.5 rounded-lg text-sm font-semibold bg-institutional-navy text-white hover:bg-institutional-navy/90 transition-colors shadow-xs"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Retry Component</span>
          </button>
          <Link
            href="/"
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-5 py-2.5 rounded-lg text-sm font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
          >
            <Home className="w-4 h-4" />
            <span>Return to Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  );
}

