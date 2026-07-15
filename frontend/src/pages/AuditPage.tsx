/**
 * Audit Logs Page — Requirement 6: Governance.
 *
 * Shows complete audit trail for an application:
 *   • Application ID, action, timestamp
 *   • SHA-256 snapshot hash (tamper-proof)
 *   • Full details JSON expandable
 */

import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getAuditTrail, type AuditLog } from '../api/client'
import { Card, Alert, Spinner } from '../components/ui'

export default function AuditPage() {
  const { id } = useParams<{ id: string }>()
  const appId = id ? Number(id) : null

  const [logs, setLogs] = useState<AuditLog[]>([])
  const [expanded, setExpanded] = useState<Record<number, boolean>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!appId) {
      setLoading(false)
      return
    }
    getAuditTrail(appId)
      .then((r) => setLogs(r.audit_logs))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [appId])

  function toggleExpand(id: number) {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  if (loading) return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-3">
        {appId && (
          <Link to={`/applications/${appId}`} className="text-blue-600 text-sm hover:underline">
            ← Back
          </Link>
        )}
        <h1 className="text-2xl font-bold text-slate-800">Audit Trail</h1>
        {appId && <span className="text-sm text-slate-500">Application #{appId}</span>}
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {/* Governance explanation */}
      <Card title="Governance Ledger (Req 6)">
        <div className="space-y-1 text-sm text-slate-600">
          {[
            '📌 Every agent action is recorded with a cryptographic SHA-256 hash.',
            '📌 Hashes prevent tampering — any modification is detectable.',
            '📌 Records include: applicant details, documents, scores, AI recommendation, fairness check, human decision.',
            '📌 Complete traceable audit trail from submission to final decision.',
          ].map((t, i) => (
            <p key={i}>{t}</p>
          ))}
        </div>
      </Card>

      {logs.length === 0 ? (
        <Alert type="warning">
          {appId
            ? 'No audit logs yet. Run the AI workflow to create audit entries.'
            : 'Select an application to view its audit trail.'}
        </Alert>
      ) : (
        <div className="space-y-3">
          {logs.map((log, idx) => (
            <div
              key={log.id}
              className="bg-white border border-slate-200 rounded-xl overflow-hidden"
            >
              {/* Log header */}
              <div
                className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-slate-50"
                onClick={() => toggleExpand(log.id)}
              >
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-bold flex items-center justify-center">
                    {idx + 1}
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{log.action}</p>
                    <p className="text-xs text-slate-400">
                      {new Date(log.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs text-slate-400 hidden sm:block">
                    {log.hash?.slice(0, 12)}…
                  </span>
                  <span className="text-xs text-slate-500">
                    {expanded[log.id] ? '▲ Collapse' : '▼ Expand'}
                  </span>
                </div>
              </div>

              {/* Expanded details */}
              {expanded[log.id] && (
                <div className="border-t border-slate-100 px-4 py-3">
                  <div className="mb-2">
                    <span className="text-xs font-medium text-slate-500">SHA-256 Hash: </span>
                    <span className="font-mono text-xs text-slate-700 break-all">
                      {log.hash}
                    </span>
                  </div>
                  <pre className="text-xs text-slate-600 bg-slate-50 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap max-h-64">
                    {JSON.stringify(log.details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
