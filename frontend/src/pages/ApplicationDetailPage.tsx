/**
 * Application Detail Page — shows full workflow state for a single application.
 * Links to Validation, Scoring, Recommendation, Fairness, Human Decision, and Audit pages.
 */

import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  getApplication,
  getDocuments,
  getRecommendation,
  processApplication,
  type Application,
  type Document,
} from '../api/client'
import {
  Card,
  StatusBadge,
  Spinner,
  Alert,
  WorkflowProgress,
  RecommendationBadge,
} from '../components/ui'
import { useAuth } from '../context/AuthContext'

function stageIndex(status: string): number {
  const map: Record<string, number> = {
    DRAFT: 0,
    SUBMITTED: 1,
    HOLD: 2,
    PENDING_REVIEW: 6,
    IN_REVIEW: 6,
    REFER: 7,
    APPROVED: 7,
    DECLINED: 7,
    FAILED: 1,
  }
  return map[status] ?? 1
}

export default function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const appId = Number(id)
  const { user } = useAuth()

  const [app, setApp] = useState<Application | null>(null)
  const [docs, setDocs] = useState<Document[]>([])
  const [recommendation, setRecommendation] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      getApplication(appId),
      getDocuments(appId),
      getRecommendation(appId).catch(() => null),
    ])
      .then(([a, d, r]) => {
        setApp(a)
        setDocs(d)
        setRecommendation(r as Record<string, unknown> | null)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [appId])

  async function handleProcess() {
    setProcessing(true)
    setError(null)
    try {
      const result = await processApplication(appId)
      setSuccess(`Workflow complete! Final status: ${result.final_status}`)
      const [a, r] = await Promise.all([
        getApplication(appId),
        getRecommendation(appId).catch(() => null),
      ])
      setApp(a)
      setRecommendation(r as Record<string, unknown> | null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Processing failed')
    } finally {
      setProcessing(false)
    }
  }

  const canProcess = user?.role === 'Underwriter' || user?.role === 'CreditManager'

  if (loading) return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>
  if (!app) return <Alert type="error">Application not found</Alert>

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <div className="flex items-center gap-3">
            <Link to="/applications" className="text-blue-600 text-sm hover:underline">
              ← Back
            </Link>
            <h1 className="text-2xl font-bold text-slate-800">Application #{app.id}</h1>
            <StatusBadge status={app.status} />
          </div>
          <p className="text-slate-500 text-sm mt-1">{app.loan_purpose}</p>
        </div>
        <div className="flex gap-2">
          {canProcess && (app.status === 'SUBMITTED' || app.status === 'DRAFT') && (
            <button
              onClick={handleProcess}
              disabled={processing}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white text-sm font-medium rounded-lg"
            >
              {processing ? <Spinner size="sm" /> : '▶ Run AI Workflow'}
            </button>
          )}
        </div>
      </div>

      {error && <Alert type="error">{error}</Alert>}
      {success && <Alert type="success">{success}</Alert>}

      {/* Workflow progress */}
      <Card title="Workflow Progress">
        <WorkflowProgress currentStage={stageIndex(app.status)} />
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Application details */}
        <Card title="Loan Details">
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-500">Loan Amount</dt>
              <dd className="font-semibold">₹{app.loan_amount.toLocaleString()}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Purpose</dt>
              <dd className="font-semibold">{app.loan_purpose}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Term</dt>
              <dd className="font-semibold">{app.term_months} months</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Monthly Debt</dt>
              <dd className="font-semibold">₹{app.monthly_debt_obligations.toLocaleString()}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Submitted</dt>
              <dd className="text-xs">{new Date(app.created_at).toLocaleString()}</dd>
            </div>
          </dl>
        </Card>

        {/* Documents */}
        <Card title="Uploaded Documents">
          {docs.length === 0 ? (
            <p className="text-slate-400 text-sm">No documents uploaded yet.</p>
          ) : (
            <ul className="space-y-2">
              {docs.map((d) => (
                <li key={d.id} className="flex items-center gap-2 text-sm">
                  <span className="text-lg">📄</span>
                  <span className="font-medium text-slate-700">{d.document_type}</span>
                  <StatusBadge status={d.status} />
                </li>
              ))}
            </ul>
          )}
          {user?.role === 'Applicant' && (
            <Link
              to="/upload"
              className="mt-3 block text-xs text-blue-600 hover:underline"
            >
              + Upload more documents
            </Link>
          )}
        </Card>
      </div>

      {/* AI Recommendation preview */}
      {recommendation?.recommendation && (
        <Card title="AI Recommendation">
          <div className="flex items-center gap-4 flex-wrap">
            <RecommendationBadge rec={String(recommendation.recommendation)} size="lg" />
            <div>
              <p className="text-sm text-slate-600">{String(recommendation.reason ?? '')}</p>
              <p className="text-xs text-slate-400 mt-1">
                Confidence: {((Number(recommendation.confidence) || 0) * 100).toFixed(0)}%
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Quick navigation to workflow pages */}
      <Card title="Workflow Details">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {[
            { to: `/validation/${appId}`, icon: '🔍', label: 'Document Validation' },
            { to: `/scoring/${appId}`, icon: '📊', label: 'Policy Scoring' },
            { to: `/recommendation/${appId}`, icon: '🤖', label: 'AI Recommendation' },
            { to: `/fairness/${appId}`, icon: '⚖️', label: 'Fairness Check' },
            { to: `/human-review/${appId}`, icon: '👨‍⚖️', label: 'Human Decision' },
            { to: `/audit/${appId}`, icon: '📜', label: 'Audit Trail' },
          ].map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className="flex flex-col items-center p-4 border border-slate-200 rounded-xl hover:border-blue-300 hover:bg-blue-50 transition-colors text-center"
            >
              <span className="text-2xl mb-1">{item.icon}</span>
              <span className="text-xs font-medium text-slate-700">{item.label}</span>
            </Link>
          ))}
        </div>
      </Card>
    </div>
  )
}
