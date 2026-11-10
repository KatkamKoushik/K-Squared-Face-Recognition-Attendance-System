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

export default async function AuditLogsPage() {
  const serverEvents = await getAuditEvents();
  const isLive = serverEvents !== null;

  const logs: AuditLogEntry[] = (serverEvents || []).map((evt) => ({
    id: evt.id,
    timestamp: evt.timestamp,
    actorId: evt.actor_id,
    actorRole: evt.actor_role,
    action: evt.action,
    resourceId: evt.resource_id,
    reason: evt.reason,
    transactionHash: evt.transaction_hash,
  }));

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
              {isLive ? "LIVE AUDIT LEDGER" : "AUDIT DATABASE"}
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
          Showing {logs.length} immutable ledger events
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
            {logs.length > 0 ? (
              logs.map((log) => (
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
              ))
            ) : (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                  No audit events recorded yet in the authoritative ledger.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
