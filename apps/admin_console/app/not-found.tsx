import React from "react";
import Link from "next/link";
import { FileQuestion, Home } from "lucide-react";

export default function NotFoundPage() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-2xl border border-slate-200 shadow-xs p-8 text-center space-y-5">
        <div className="w-14 h-14 mx-auto rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-institutional-navy">
          <FileQuestion className="w-8 h-8" />
        </div>

        <div>
          <h2 className="font-serif text-2xl font-bold text-institutional-navy">
            Resource Not Found (404)
          </h2>
          <p className="text-sm text-institutional-muted mt-2">
            The requested institutional view, offering path, or academic record could not be found or has been relocated.
          </p>
        </div>

        <div className="pt-2">
          <Link
            href="/"
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg text-sm font-semibold bg-institutional-navy text-white hover:bg-institutional-navy/90 transition-colors shadow-xs"
          >
            <Home className="w-4 h-4" />
            <span>Return to Executive Overview</span>
          </Link>
        </div>
      </div>
    </div>
  );
}

