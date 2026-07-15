/**
 * Human Decision Page — Requirement 4: Human Gate.
 *
 * The AI NEVER approves or declines a loan.
 * Only a licensed human underwriter makes the final decision.
 *
 * Interface shows:
 *   • AI Recommendation
 *   • Score breakdown
 *   • Decision buttons: Approve / Refer / Decline
 *   • Comment box
 *   • Save Decision
 */

import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  getRecommendation,
  submitHumanReview,
  getApplication,
  type Application,
} from '../api/client'
import {
  Card,
  Alert,
  Spinner,
  RecommendationBadge,
  StatusBadge,
  PolicyScoreTable,
} from '../components/ui'
import { clsx } from 'clsx'
import { useAuth } from '../context/AuthContext'

type DecisionType = 'APPROVE' | 'REFER' | 'DECLINE'

export default function HumanReviewPage() {
  const { id } = useParams<{ id: string }>()
  const appId = Number(id)
  const { user } = useAuth()

  const [app, setApp] = useState<Application | null>(null)
  const [recData, setRecData] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [decision, setDecision] = useState<DecisionType | null>(null)
  const [comment, setComment] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const canDecide = user?.role === 'Underwriter' || user?.role === 'CreditManager'

  useEffect(() => {
    Promise.all([
      getApplication(appId),
      getRecommendation(appId).catch(() => null),
    ])
      .then(([a, r]) => {
        setApp(a)
        setRecData(r as Record<string, unknown> | null)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [appId])

  async function handleSubmit() {
    if (!decision) return
    setSubmitting(true)
    setError(null)
    try {
      const result = await submitHumanReview(appId, decision, comment || undefined)
      setSuccess(
        `Decision recorded: ${result.decision} — Application status: ${result.status}`
      )
      const updated = await getApplication(appId)
      setApp(updated)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to submit decision')
    } finally {
      setSubmitting(false)
    }
  }

  const aiRec = recData?.recommendation as string | undefined
  const scores = recData?.score_breakdown as Parameters<typeof PolicyScoreTable>[0]['scores'] | undefined

  if (loading) return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-3 flex-wrap">
        <Link to={`/applications/${appId}`} className="text-blue-600 text-sm hover:underline">← Back</Link>
        <h1 className="text-2xl font-bold text-slate-800">Human Decision</h1>
        <span className="text-sm text-slate-500">Application #{appId}</span>
        {app && <StatusBadge status={app.status} />}
      </div>

      {error && <Alert type="error">{error}</Alert>}
      {success && <Alert type="success">{success}</Alert>}

      {/* Human Gate notice */}
      <Alert type="info">
        <strong>🏛️ Human Gate — Requirement 4</strong>
        <p className="mt-1 text-sm">
          The AI system has produced a recommendation. A licensed human underwriter
          must review the AI recommendation and make the final decision.
          The AI will <strong>never</strong> approve or reject a loan autonomously.
        </p>
      </Alert>

      {/* AI Recommendation display */}
      <Card title="AI Recommendation (for reference)">
        {aiRec ? (
          <div className="flex items-center gap-4 flex-wrap">
            <div className="text-center">
              <p className="text-xs text-slate-500 mb-1.5">AI Recommends</p>
              <RecommendationBadge rec={aiRec} size="lg" />
            </div>
            <div className="flex-1">
              <p className="text-sm text-slate-600">{String(recData?.reason ?? '')}</p>
              <div className="flex gap-1.5 mt-2 flex-wrap">
                {((recData?.policy_citations as string[]) ?? []).map((c) => (
                  <span key={c} className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                    {c}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <Alert type="warning">
            No AI recommendation available. Run the workflow first.
          </Alert>
        )}
      </Card>

      {/* Score summary */}
      {scores?.criteria && scores.criteria.length > 0 && (
        <Card title="Score Breakdown">
          <PolicyScoreTable scores={scores} />
        </Card>
      )}

      {/* Human Decision Interface — Req 4 */}
      {canDecide && (
        <Card title="Underwriter Decision">
          {success ? (
            <Alert type="success">{success}</Alert>
          ) : (
            <div className="space-y-5">
              {/* Decision buttons */}
              <div>
                <p className="text-sm font-medium text-slate-700 mb-3">
                  Select your decision:
                </p>
                <div className="grid grid-cols-3 gap-3">
                  {(['APPROVE', 'REFER', 'DECLINE'] as DecisionType[]).map((d) => {
                    const colors: Record<DecisionType, string> = {
                      APPROVE: 'border-green-400 bg-green-50 text-green-700',
                      REFER: 'border-amber-400 bg-amber-50 text-amber-700',
                      DECLINE: 'border-red-400 bg-red-50 text-red-700',
                    }
                    const selected: Record<DecisionType, string> = {
                      APPROVE: 'ring-2 ring-green-500 bg-green-100',
                      REFER: 'ring-2 ring-amber-500 bg-amber-100',
                      DECLINE: 'ring-2 ring-red-500 bg-red-100',
                    }
                    const icons: Record<DecisionType, string> = {
                      APPROVE: '✅',
                      REFER: '↩️',
                      DECLINE: '❌',
                    }
                    return (
                      <button
                        key={d}
                        onClick={() => setDecision(d)}
                        className={clsx(
                          'py-4 rounded-xl border-2 font-bold text-sm transition-all',
                          colors[d],
                          decision === d && selected[d]
                        )}
                      >
                        <div className="text-2xl mb-1">{icons[d]}</div>
                        {d}
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Reason / comment */}
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">
                  Decision Reason / Comment
                </label>
                <textarea
                  rows={3}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Enter your reasoning for this decision (optional but recommended)..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Save button */}
              <button
                onClick={handleSubmit}
                disabled={!decision || submitting}
                className="w-full py-3 bg-slate-800 hover:bg-slate-900 disabled:opacity-50 text-white font-bold rounded-xl transition-colors"
              >
                {submitting ? (
                  <Spinner size="sm" />
                ) : decision ? (
                  `💾 Save Decision: ${decision}`
                ) : (
                  'Select a Decision Above'
                )}
              </button>
            </div>
          )}
        </Card>
      )}

      {!canDecide && (
        <Alert type="info">
          Only Underwriters and Credit Managers can submit decisions.
          Your role ({user?.role}) can view this page but cannot submit decisions.
        </Alert>
      )}
    </div>
  )
}
