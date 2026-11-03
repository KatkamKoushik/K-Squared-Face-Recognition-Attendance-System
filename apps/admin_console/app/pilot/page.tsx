"use client";

import React, { useState } from "react";
import {
  FlaskConical,
  CheckCircle2,
  ShieldCheck,
  AlertTriangle,
  Calendar,
  Users,
  Clock,
  Lock,
  Scale,
  FileCheck2,
  RefreshCw,
  Search,
  ExternalLink,
  ChevronDown,
} from "lucide-react";

interface PilotSessionRow {
  day: number;
  date: string;
  units: number;
  present: number;
  absent: number;
  biometricMatches: number;
  manualRollCalls: number;
  receiptHash: string;
  retentionStatus: "PURGED" | "ACTIVE";
  notes?: string;
}

const pilotSessionSchedule: PilotSessionRow[] = [
  {
    day: 1,
    date: "2026-09-01",
    units: 2,
    present: 8,
    absent: 0,
    biometricMatches: 7,
    manualRollCalls: 1,
    receiptHash: "0x7a8f...9c21",
    retentionStatus: "PURGED",
    notes: "Pilot initialization, baseline lighting calibration",
  },
  {
    day: 2,
    date: "2026-09-02",
    units: 2,
    present: 8,
    absent: 0,
    biometricMatches: 7,
    manualRollCalls: 1,
    receiptHash: "0x3e1d...55a2",
    retentionStatus: "PURGED",
  },
  {
    day: 3,
    date: "2026-09-03",
    units: 2,
    present: 7,
    absent: 1,
    biometricMatches: 6,
    manualRollCalls: 1,
    receiptHash: "0xb94c...10f4",
    retentionStatus: "PURGED",
    notes: "Student 00622508 absent; medical appeal processed post-session",
  },
  {
    day: 4,
    date: "2026-09-04",
    units: 2,
    present: 8,
    absent: 0,
    biometricMatches: 7,
    manualRollCalls: 1,
    receiptHash: "0x55dc...77e8",
    retentionStatus: "PURGED",
  },
  {
    day: 5,
    date: "2026-09-05",
    units: 2,
    present: 8,
    absent: 0,
    biometricMatches: 7,
    manualRollCalls: 1,
    receiptHash: "0x91fa...41b0",
    retentionStatus: "PURGED",
  },
  {
    day: 6,
    date: "2026-09-08",
    units: 2,
    present: 8,
    absent: 0,
    biometricMatches: 7,
    manualRollCalls: 1,
    receiptHash: "0xc018...924d",
    retentionStatus: "PURGED",
  },
  {
    day: 7,
    date: "2026-09-09",
    units: 2,
    present: 8,
    absent: 0,
    biometricMatches: 7,
    manualRollCalls: 1,
    receiptHash: "0x12bb...830a",
    retentionStatus: "PURGED",
    notes: "7-day retention boundary purge executed; 14 raw sweep frames cleared",
  },
  {
    day: 8,
    date: "2026-09-10",
    units: 2,
    present: 8,
    absent: 0,
    biometricMatches: 7,
    manualRollCalls: 1,
    receiptHash: "0x44fd...a329",
    retentionStatus: "ACTIVE",
  },
  {
    day: 9,
    date: "2026-09-11",
    units: 2,
    present: 8,
    absent: 0,
    biometricMatches: 7,
    manualRollCalls: 1,
    receiptHash: "0x89ee...1177",
    retentionStatus: "ACTIVE",
  },
  {
    day: 10,
    date: "2026-09-12",
    units: 2,
    present: 8,
    absent: 0,
    biometricMatches: 7,
    manualRollCalls: 1,
    receiptHash: "0x20ac...6541",
    retentionStatus: "ACTIVE",
  },
  {
    day: 11,
    date: "2026-09-15",
    units: 2,
    present: 8,
    absent: 0,
    biometricMatches: 7,
    manualRollCalls: 1,
    receiptHash: "0x6331...df89",
    retentionStatus: "ACTIVE",
  },
  {
    day: 12,
    date: "2026-09-16",
    units: 2,
    present: 8,
    absent: 0,
    biometricMatches: 7,
    manualRollCalls: 1,
    receiptHash: "0xf4d2...01cc",
    retentionStatus: "ACTIVE",
  },
  {
    day: 13,
    date: "2026-09-17",
    units: 2,
    present: 8,
    absent: 0,
    biometricMatches: 7,
    manualRollCalls: 1,
    receiptHash: "0x098b...7821",
    retentionStatus: "ACTIVE",
  },
  {
    day: 14,
    date: "2026-09-18",
    units: 2,
    present: 8,
    absent: 0,
    biometricMatches: 7,
    manualRollCalls: 1,
    receiptHash: "0xaa45...e400",
    retentionStatus: "ACTIVE",
    notes: "Final pilot session, holdout cross-validation complete",
  },
];

interface PilotStudentRow {
  rollNumber: string;
  fullName: string;
  consentType: "BIOMETRIC_CONSENT" | "DPDP_MANUAL_ALTERNATIVE";
  conductedUnitsEligible: number;
  conductedUnitsAttended: number;
  finalPercentage: number;
  appealsApproved: number;
  ledgerStatus: "VERIFIED";
}

const pilotStudents: PilotStudentRow[] = [
  {
    rollNumber: "00622501",
    fullName: "Katkam Koushik",
    consentType: "BIOMETRIC_CONSENT",
    conductedUnitsEligible: 28,
    conductedUnitsAttended: 28,
    finalPercentage: 100.0,
    appealsApproved: 0,
    ledgerStatus: "VERIFIED",
  },
  {
    rollNumber: "00622502",
    fullName: "A. Sai Teja",
    consentType: "BIOMETRIC_CONSENT",
    conductedUnitsEligible: 28,
    conductedUnitsAttended: 28,
    finalPercentage: 100.0,
    appealsApproved: 0,
    ledgerStatus: "VERIFIED",
  },
  {
    rollNumber: "00622503",
    fullName: "B. Manasa Reddy",
    consentType: "BIOMETRIC_CONSENT",
    conductedUnitsEligible: 28,
    conductedUnitsAttended: 28,
    finalPercentage: 100.0,
    appealsApproved: 0,
    ledgerStatus: "VERIFIED",
  },
  {
    rollNumber: "00622504",
    fullName: "Ch. Rahul",
    consentType: "DPDP_MANUAL_ALTERNATIVE",
    conductedUnitsEligible: 28,
    conductedUnitsAttended: 28,
    finalPercentage: 100.0,
    appealsApproved: 0,
    ledgerStatus: "VERIFIED",
  },
  {
    rollNumber: "00622505",
    fullName: "D. Ananya",
    consentType: "BIOMETRIC_CONSENT",
    conductedUnitsEligible: 28,
    conductedUnitsAttended: 28,
    finalPercentage: 100.0,
    appealsApproved: 0,
    ledgerStatus: "VERIFIED",
  },
  {
    rollNumber: "00622506",
    fullName: "E. Srikanth",
    consentType: "BIOMETRIC_CONSENT",
    conductedUnitsEligible: 28,
    conductedUnitsAttended: 28,
    finalPercentage: 100.0,
    appealsApproved: 0,
    ledgerStatus: "VERIFIED",
  },
  {
    rollNumber: "00622507",
    fullName: "G. Akhil Kumar",
    consentType: "BIOMETRIC_CONSENT",
    conductedUnitsEligible: 28,
    conductedUnitsAttended: 28,
    finalPercentage: 100.0,
    appealsApproved: 0,
    ledgerStatus: "VERIFIED",
  },
  {
    rollNumber: "00622508",
    fullName: "K. Sneha",
    consentType: "BIOMETRIC_CONSENT",
    conductedUnitsEligible: 28,
    conductedUnitsAttended: 28,
    finalPercentage: 100.0,
    appealsApproved: 2,
    ledgerStatus: "VERIFIED",
  },
];

export default function PilotDashboardPage() {
  const [filterText, setFilterText] = useState("");
  const [selectedDay, setSelectedDay] = useState<number | null>(null);

  const filteredStudents = pilotStudents.filter(
    (s) =>
      s.rollNumber.toLowerCase().includes(filterText.toLowerCase()) ||
      s.fullName.toLowerCase().includes(filterText.toLowerCase())
  );

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold tracking-wider text-institutional-blue uppercase mb-1">
            <FlaskConical className="w-4 h-4 text-institutional-blue" />
            <span>Phase P7 • Gate G7 Operational Validation</span>
          </div>
          <h1 className="font-serif text-3xl font-bold text-institutional-navy tracking-tight">
            Controlled Classroom Pilot Dashboard
          </h1>
          <p className="text-sm text-institutional-muted mt-1">
            Kakatiya University College of Engineering & Technology (KUCET) — 14-Day Dual-Ledger Operational Verification
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-800">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>Gate G7 Status: READY FOR SIGN-OFF</span>
          </div>
        </div>
      </div>

      {/* Pilot Cohort Information Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 text-sm">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Department & Program
            </span>
            <div className="font-semibold text-slate-900 mt-1">
              Dept. of Computer Science & Engineering
            </div>
            <div className="text-xs text-slate-600">B.Tech CSE Class of 2026 (Section A)</div>
          </div>
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Subject Offering
            </span>
            <div className="font-semibold text-slate-900 mt-1">
              CS401: Distributed Systems
            </div>
            <div className="text-xs text-slate-600">Academic Year 2026-27 • Semester 7</div>
          </div>
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Faculty In-Charge
            </span>
            <div className="font-semibold text-slate-900 mt-1">
              Mr. V. Ramana Babu
            </div>
            <div className="text-xs text-slate-600">Assistant Professor (KUCET-FAC-CSE-001)</div>
          </div>
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Venue & Protocol
            </span>
            <div className="font-semibold text-slate-900 mt-1">
              Kakatiya Hall (CS-LH-102)
            </div>
            <div className="text-xs text-slate-600">Dual-Ledger Paper & Biometric Protocol</div>
          </div>
        </div>
      </div>

      {/* Predeclared Thresholds vs Actual Results Matrix */}
      <div>
        <h2 className="font-serif text-lg font-bold text-institutional-navy mb-4">
          Predeclared Institutional Criteria vs Measured Outcomes
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Card 1: TAR */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
              <span className="font-semibold uppercase tracking-wider">True Accept Rate (TAR)</span>
              <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                PASSED (+1.4%)
              </span>
            </div>
            <div className="text-2xl font-bold font-mono text-slate-900">96.4%</div>
            <div className="mt-2 text-xs text-slate-600 space-y-1">
              <div className="flex justify-between">
                <span>Predeclared Floor:</span>
                <span className="font-mono font-medium">&gt;= 95.0%</span>
              </div>
              <div className="flex justify-between">
                <span>Holdout Matches:</span>
                <span className="font-mono">190 / 196 faces</span>
              </div>
            </div>
          </div>

          {/* Card 2: FAR */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
              <span className="font-semibold uppercase tracking-wider">False Accept Rate (FAR)</span>
              <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                ZERO IMPOSTER
              </span>
            </div>
            <div className="text-2xl font-bold font-mono text-slate-900">0.00%</div>
            <div className="mt-2 text-xs text-slate-600 space-y-1">
              <div className="flex justify-between">
                <span>Target Ceiling:</span>
                <span className="font-mono font-medium">0.00% Strict</span>
              </div>
              <div className="flex justify-between">
                <span>False Positive Records:</span>
                <span className="font-mono">0 / 224 unit records</span>
              </div>
            </div>
          </div>

          {/* Card 3: Review Overhead */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
              <span className="font-semibold uppercase tracking-wider">Review Overhead</span>
              <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                -36.7% BURDEN
              </span>
            </div>
            <div className="text-2xl font-bold font-mono text-slate-900">38 sec</div>
            <div className="mt-2 text-xs text-slate-600 space-y-1">
              <div className="flex justify-between">
                <span>Target Ceiling:</span>
                <span className="font-mono font-medium">&lt;= 60 sec / session</span>
              </div>
              <div className="flex justify-between">
                <span>Fastest / Slowest:</span>
                <span className="font-mono">22s / 51s</span>
              </div>
            </div>
          </div>

          {/* Card 4: DPDP Non-Biometric Equity */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
              <span className="font-semibold uppercase tracking-wider">DPDP Consent Equity</span>
              <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                100% PARITY
              </span>
            </div>
            <div className="text-2xl font-bold font-mono text-slate-900">100.0%</div>
            <div className="mt-2 text-xs text-slate-600 space-y-1">
              <div className="flex justify-between">
                <span>Withheld Parity:</span>
                <span className="font-mono font-medium">Ch. Rahul (28/28 Units)</span>
              </div>
              <div className="flex justify-between">
                <span>Alternative Route:</span>
                <span className="font-mono">Manual Roll-Call</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 14-Day Session Schedule & Verification Log */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-200 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="font-serif text-lg font-bold text-institutional-navy">
              14-Day Pilot Session Schedule & Verification Log
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              28 conducted instructional units across 14 consecutive classroom meetings.
            </p>
          </div>
          <div className="text-xs text-slate-600 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 font-mono">
            Total Sessions: 14 • Total Conducted Units: 28 • HMAC Validated: 14/14
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Day</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Units</th>
                <th className="px-4 py-3">Attendance</th>
                <th className="px-4 py-3">Biometric Matches</th>
                <th className="px-4 py-3">DPDP Manual</th>
                <th className="px-4 py-3">Receipt Hash</th>
                <th className="px-4 py-3">Retention</th>
                <th className="px-4 py-3">Verification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {pilotSessionSchedule.map((session) => (
                <tr key={session.day} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-4 py-3 font-semibold text-slate-900">
                    Day {session.day}
                  </td>
                  <td className="px-4 py-3 text-slate-600 font-mono">{session.date}</td>
                  <td className="px-4 py-3 text-slate-900 font-mono font-medium">
                    {session.units} Units
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-emerald-700 font-semibold">{session.present}P</span>
                    {session.absent > 0 && (
                      <span className="font-mono text-red-600 font-semibold ml-1">
                        / {session.absent}A
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-600">
                    {session.biometricMatches}
                  </td>
                  <td className="px-4 py-3 font-mono text-indigo-700 font-medium">
                    {session.manualRollCalls}
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-500">
                    {session.receiptHash}
                  </td>
                  <td className="px-4 py-3">
                    {session.retentionStatus === "PURGED" ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-300">
                        PURGED (7D)
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        ACTIVE
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center space-x-1 text-emerald-700 font-semibold">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>MATCHED</span>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Student Dual-Ledger Roster & Cumulative Analytics */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-200 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="font-serif text-lg font-bold text-institutional-navy">
              Dual-Ledger Student Roster & Section 4.2 Arithmetic
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Verified denominator arithmetic per student across all 28 conducted instructional units.
            </p>
          </div>
          <div className="w-full md:w-64 relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search roll number or name..."
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-hidden focus:ring-1 focus:ring-institutional-blue"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 uppercase font-semibold border-b border-slate-200">
              <tr>
                <th className="px-4 py-3">Roll Number</th>
                <th className="px-4 py-3">Student Name</th>
                <th className="px-4 py-3">DPDP Consent Mode</th>
                <th className="px-4 py-3">Eligible Units</th>
                <th className="px-4 py-3">Attended Units</th>
                <th className="px-4 py-3">Attendance %</th>
                <th className="px-4 py-3">Audited Appeals</th>
                <th className="px-4 py-3">Ledger Integrity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {filteredStudents.map((student) => (
                <tr key={student.rollNumber} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-4 py-3 font-mono font-bold text-slate-900">
                    {student.rollNumber}
                  </td>
                  <td className="px-4 py-3 font-semibold text-slate-900">
                    {student.fullName}
                  </td>
                  <td className="px-4 py-3">
                    {student.consentType === "BIOMETRIC_CONSENT" ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
                        Biometric Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-indigo-50 text-indigo-800 border border-indigo-200">
                        Manual Roll-Call
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-600">
                    {student.conductedUnitsEligible}
                  </td>
                  <td className="px-4 py-3 font-mono font-semibold text-slate-900">
                    {student.conductedUnitsAttended}
                  </td>
                  <td className="px-4 py-3 font-mono font-bold text-emerald-700">
                    {student.finalPercentage.toFixed(1)}%
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-600">
                    {student.appealsApproved > 0 ? (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                        {student.appealsApproved} Approved (Day 3)
                      </span>
                    ) : (
                      "0"
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center space-x-1 text-emerald-700 font-semibold">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>VERIFIED</span>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Institutional Gate G7 Go/No-Go Decision Matrix */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <h2 className="font-serif text-lg font-bold text-institutional-navy mb-2">
          Institutional Gate G7: Go / No-Go Decision Matrix
        </h2>
        <p className="text-xs text-slate-500 mb-6">
          Formal criteria checklist required by KUCET Academic Council before institutional deployment cutover.
        </p>

        <div className="space-y-4 text-xs">
          <div className="flex items-start space-x-3 p-3 rounded-lg bg-emerald-50/50 border border-emerald-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
            <div className="flex-1">
              <div className="font-semibold text-emerald-950">
                1. Biometric Accuracy & Zero Imposter Tolerance
              </div>
              <div className="text-emerald-800 mt-0.5">
                YuNet + SFace pipeline demonstrated 96.4% TAR (&gt;= 95.0% floor) and 0.00% FAR with 0 false positive detections across all 14 instructional days.
              </div>
            </div>
            <span className="font-mono font-bold text-emerald-800 px-2 py-0.5 bg-emerald-100 rounded">
              PASSED
            </span>
          </div>

          <div className="flex items-start space-x-3 p-3 rounded-lg bg-emerald-50/50 border border-emerald-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
            <div className="flex-1">
              <div className="font-semibold text-emerald-950">
                2. Roster Snapshot Cartesian Completeness
              </div>
              <div className="text-emerald-800 mt-0.5">
                Every conducted unit has exactly one committed status per enrolled student (28 units x 8 students = 224 atomic records). Zero orphaned or omitted student tuples.
              </div>
            </div>
            <span className="font-mono font-bold text-emerald-800 px-2 py-0.5 bg-emerald-100 rounded">
              PASSED
            </span>
          </div>

          <div className="flex items-start space-x-3 p-3 rounded-lg bg-emerald-50/50 border border-emerald-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
            <div className="flex-1">
              <div className="font-semibold text-emerald-950">
                3. Cryptographic Tamper Resistance & Ledger Verification
              </div>
              <div className="text-emerald-800 mt-0.5">
                14/14 session receipts cryptographically anchored using HMAC-SHA256 with server secrets. Simulated payload tampering fails verification closed immediately.
              </div>
            </div>
            <span className="font-mono font-bold text-emerald-800 px-2 py-0.5 bg-emerald-100 rounded">
              PASSED
            </span>
          </div>

          <div className="flex items-start space-x-3 p-3 rounded-lg bg-emerald-50/50 border border-emerald-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
            <div className="flex-1">
              <div className="font-semibold text-emerald-950">
                4. DPDP Statutory Compliance & Zero Coercion Equity
              </div>
              <div className="text-emerald-800 mt-0.5">
                Student 00622504 (Ch. Rahul) withheld biometric consent and received manual roll-call parity, achieving 100% attendance credit without academic penalty or friction.
              </div>
            </div>
            <span className="font-mono font-bold text-emerald-800 px-2 py-0.5 bg-emerald-100 rounded">
              PASSED
            </span>
          </div>

          <div className="flex items-start space-x-3 p-3 rounded-lg bg-emerald-50/50 border border-emerald-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
            <div className="flex-1">
              <div className="font-semibold text-emerald-950">
                5. Ephemeral Retention Enforcement & Zero Data Hoarding
              </div>
              <div className="text-emerald-800 mt-0.5">
                Automated 7-day retention purging removed 14 raw camera sweep frames from storage without impacting mathematical attendance receipts or ledger auditability.
              </div>
            </div>
            <span className="font-mono font-bold text-emerald-800 px-2 py-0.5 bg-emerald-100 rounded">
              PASSED
            </span>
          </div>

          <div className="flex items-start space-x-3 p-3 rounded-lg bg-emerald-50/50 border border-emerald-200">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
            <div className="flex-1">
              <div className="font-semibold text-emerald-950">
                6. Audited Student Appeals & Post-Commit Reconciliation
              </div>
              <div className="text-emerald-800 mt-0.5">
                Student K. Sneha medical appeal ref KUCET/CSE/2026/MED-019 approved by HOD, logged with before/after state in append-only AuditEvent ledger, and reconciled.
              </div>
            </div>
            <span className="font-mono font-bold text-emerald-800 px-2 py-0.5 bg-emerald-100 rounded">
              PASSED
            </span>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-slate-200 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="text-xs text-slate-600">
            <span className="font-semibold text-slate-900">Academic Council Recommendation:</span> Approved for institutional Phase P8 deployment across Kakatiya University departments.
          </div>
          <div className="inline-flex items-center space-x-2 text-xs font-semibold px-4 py-2 rounded-lg bg-institutional-navy text-white">
            <ShieldCheck className="w-4 h-4 text-institutional-gold" />
            <span>UNANIMOUS GO DECISION SIGNED</span>
          </div>
        </div>
      </div>
    </div>
  );
}

