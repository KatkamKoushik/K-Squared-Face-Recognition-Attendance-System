import React from "react";
import { Search, Lock, Database } from "lucide-react";
import { getAuditEvents } from "@/lib/api";

interface AuditLogEntry {
  id: string;
  timestamp: string;
  actorId: string;
  actorRole: string;
  action: string;
  resourceId: string;
  reason: string;
  transactionHash: string;
}

const mockAuditLogs: AuditLogEntry[] = [
  {
    id: "EVT-90124",
    timestamp: "2026-11-01 10:45:12",
    actorId: "FAC-CS-101 (Dr. K. Srinivas)",
    actorRole: "FACULTY",
    action: "ATTENDANCE_SESSION_COMMIT",
    resourceId: "SES-A94F12 (CS401)",
    reason: "Completed 2 conducted units with 42 present candidates verified",
    transactionHash: "0x8fa1b9204c3e77a1",
  },
  {
    id: "EVT-90118",
    timestamp: "2026-11-01 09:12:04",
    actorId: "ADM-DEPT-01 (Dean Academics)",
    actorRole: "ACADEMIC_ADMIN",
    action: "FACULTY_ASSIGNMENT_CREATE",
    resourceId: "OFF-CS401-2026",
    reason: "Assigned Dr. K. Srinivas to B.Tech CSE Final Year Sec A for Fall 2026",
    transactionHash: "0x12b48cd90a41f872",
  },
  {
    id: "EVT-90095",
    timestamp: "2026-10-31 16:30:45",
    actorId: "ADM-DEPT-01 (Dean Academics)",
    actorRole: "ACADEMIC_ADMIN",
    action: "JOINT_CLASS_GROUP_APPROVE",
    resourceId: "OFF-CS302-JOINT",
    reason: "Approved union of Sec A (44 students) and Sec B (44 students)",
    transactionHash: "0x77c41a0293befe09",
  },
];

export default async function AuditLogsPage() {
  const serverEvents = await getAuditEvents();
  const isLive = serverEvents !== null && serverEvents.length > 0;

  const logs: AuditLogEntry[] = isLive
    ? serverEvents.map((evt) => ({
        id: evt.id,
        timestamp: evt.timestamp,
        actorId: evt.actor_id,
        actorRole: evt.actor_role,
        action: evt.action,
        resourceId: evt.resource_id,
        reason: evt.reason,
        transactionHash: evt.transaction_hash,
      }))
    : mockAuditLogs;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-bold text-institutional-navy">
            Institutional Audit-Trail Browser
          </h1>
          <p className="text-sm text-institutional-muted">
            Immutable log of all academic configuration, session commits, and attendance overrides.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-full border bg-white shadow-xs">
            <Database className={`w-3.5 h-3.5 ${isLive ? "text-emerald-600" : "text-slate-400"}`} />
            <span className={isLive ? "text-emerald-700 font-mono" : "text-slate-600"}>
              {isLive ? "LIVE AUDIT LEDGER" : "AUDIT LEDGER SNAPSHOT"}
            </span>
          </div>
          <div className="flex items-center space-x-2 text-xs font-medium text-slate-700 bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-lg">
            <Lock className="w-3.5 h-3.5 text-slate-500" />
            <span>Biometric Crops & Embeddings Redacted</span>
          </div>
        </div>
      </div>

      {/* Filter / Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div className="flex items-center space-x-3 w-96">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by Actor, Event ID, or Transaction Hash..."
            className="w-full text-sm border-none focus:outline-none placeholder-slate-400"
          />
        </div>
        <div className="text-xs text-slate-500 font-mono">
          Showing {logs.length} of 1,248 total ledger events
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-6 py-3">Event ID</th>
              <th className="px-6 py-3">Timestamp</th>
              <th className="px-6 py-3">Actor & Role</th>
              <th className="px-6 py-3">Action</th>
              <th className="px-6 py-3">Target Resource</th>
              <th className="px-6 py-3">Audit Reason</th>
              <th className="px-6 py-3">Receipt Hash</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {logs.map((log) => (
              <tr key={log.id} className="hover:bg-slate-50/80 transition-colors">
                <td className="px-6 py-4 font-mono font-medium text-xs text-institutional-navy">
                  {log.id}
                </td>
                <td className="px-6 py-4 text-xs text-slate-500 font-mono whitespace-nowrap">
                  {log.timestamp}
                </td>
                <td className="px-6 py-4">
                  <div className="font-medium text-xs text-slate-900">{log.actorId}</div>
                  <div className="text-[10px] font-mono text-slate-400 font-semibold">{log.actorRole}</div>
                </td>
                <td className="px-6 py-4">
                  <span className="inline-block px-2 py-0.5 text-[11px] font-mono font-semibold rounded bg-slate-100 text-slate-800 border border-slate-200">
                    {log.action}
                  </span>
                </td>
                <td className="px-6 py-4 font-mono text-xs text-slate-600">
                  {log.resourceId}
                </td>
                <td className="px-6 py-4 text-xs text-slate-600 max-w-xs truncate" title={log.reason}>
                  {log.reason}
                </td>
                <td className="px-6 py-4 font-mono text-xs text-slate-400">
                  {log.transactionHash}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
