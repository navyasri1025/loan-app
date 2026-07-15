/**
 * Document Validation Page — Req 1.
 *
 * Shows: validation status, issues, missing documents, hold reason.
 */

import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getRecommendation } from '../api/client'
import { Card, StatusBadge, Alert, Spinner } from '../components/ui'

interface ValidationData {
  validation_status?: string
  validation_issues?: Array<{
    document_type: string
    issue_type: string
    severity: string
    message: string
  }>
  missing_documents?: string[]
  hold_reason?: string
  summary?: string
  valid_documents?: string[]
}

export default function ValidationPage() {
  const { id } = useParams<{ id: string }>()
  const appId = Number(id)

  const [data, setData] = useState<ValidationData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getRecommendation(appId)
      .then((r) => {
        const details = r.full_details as Record<string, unknown> | undefined
        const vReport = details?.validation_status
          ? details
          : null

        if (vReport) {
          setData({
            validation_status: vReport.validation_status as string,
            validation_issues: (vReport.validation_issues as ValidationData['validation_issues']) ?? [],
            missing_documents: (vReport.missing_documents as string[]) ?? [],
            hold_reason: vReport.hold_reason as string,
            summary: vReport.summary as string,
          })
        } else {
          setData(null)
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [appId])

  if (loading) return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-3">
        <Link to={`/applications/${appId}`} className="text-blue-600 text-sm hover:underline">← Back</Link>
        <h1 className="text-2xl font-bold text-slate-800">Document Validation</h1>
        <span className="text-sm text-slate-500">Application #{appId}</span>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {!data ? (
        <Alert type="warning">
          No validation data yet. Run the AI workflow first to validate documents.
        </Alert>
      ) : (
        <>
          {/* Status overview */}
          <Card title="Validation Result">
            <div className="flex items-center gap-4">
              <StatusBadge status={data.validation_status ?? 'UNKNOWN'} />
              <p className="text-sm text-slate-600">{data.summary}</p>
            </div>
          </Card>

          {/* Hold reason */}
          {data.validation_status === 'HOLD' && (
            <Alert type="warning">
              <strong>Application On Hold</strong>
              <p className="mt-1">{data.hold_reason ?? 'Missing required documents.'}</p>
              <p className="mt-1 text-xs">
                Missing: {data.missing_documents?.join(', ')}
              </p>
            </Alert>
          )}

          {/* Issues */}
          {(data.validation_issues?.length ?? 0) > 0 && (
            <Card title="Validation Issues">
              <div className="space-y-2">
                {data.validation_issues?.map((issue, idx) => (
                  <div
                    key={idx}
                    className={`flex items-start gap-3 p-3 rounded-lg ${
                      issue.severity === 'error'
                        ? 'bg-red-50 border border-red-200'
                        : 'bg-amber-50 border border-amber-200'
                    }`}
                  >
                    <span className="text-lg mt-0.5">
                      {issue.severity === 'error' ? '❌' : '⚠️'}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-slate-800">{issue.document_type}</p>
                      <p className="text-xs text-slate-600">{issue.message}</p>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Type: {issue.issue_type} • Severity: {issue.severity}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* What the validator checks — Req 1 transparency */}
          <Card title="Validation Criteria (Requirement 1)">
            <div className="space-y-2 text-sm text-slate-600">
              {[
                { icon: '🪪', text: 'Government ID — PAN or Aadhaar (presence check)' },
                { icon: '💰', text: 'Income Proof — Salary Slip or Income Certificate (presence check)' },
                { icon: '🏦', text: 'Bank Statement — 6-month statement (presence check)' },
                { icon: '✅', text: 'Consistency — name and employer match across documents' },
                { icon: '🔍', text: 'Readability — OCR confidence ≥ 70%' },
                { icon: '🚫', text: 'If any required group is missing → Application HOLD, scoring blocked' },
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span>{item.icon}</span>
                  <span>{item.text}</span>
                </div>
              ))}
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
