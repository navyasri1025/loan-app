/**
 * Recommendation Page — Requirement 3.
 *
 * Displays:
 *   • AI recommendation (APPROVE / REFER / DECLINE)
 *   • Overall score
 *   • Per-clause breakdown with explanations
 *   • Policy citations
 *   • Full reasoning
 *
 * NOTE: This is an AI RECOMMENDATION only. Human decision required.
 */

import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getRecommendation } from '../api/client'
import {
  Card,
  Alert,
  Spinner,
  RecommendationBadge,
  PolicyScoreTable,
} from '../components/ui'
import { clsx } from 'clsx'

export default function RecommendationPage() {
  const { id } = useParams<{ id: string }>()
  const appId = Number(id)

  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getRecommendation(appId)
      .then((r) => setData(r as unknown as Record<string, unknown>))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [appId])

  if (loading) return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>

  const rec = data?.recommendation as string | undefined
  const confidence = Number(data?.confidence ?? 0)
  const reason = data?.reason as string | undefined
  const citations = (data?.policy_citations as string[]) ?? []
  const scores = data?.score_breakdown as Record<string, unknown> | undefined
  const fullDetails = data?.full_details as Record<string, unknown> | undefined
  const aiRec = fullDetails?.ai_recommendation as Record<string, unknown> | undefined
  const explanation = aiRec?.explanation as string | undefined

  // Parse clause-level reasons if present (Req 3)
  const clauseReasons = (aiRec?.reasons_json as Array<{
    clause: string
    criterion: string
    pass_fail: string
    rationale: string
  }>) ?? []

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-3">
        <Link to={`/applications/${appId}`} className="text-blue-600 text-sm hover:underline">← Back</Link>
        <h1 className="text-2xl font-bold text-slate-800">AI Recommendation</h1>
        <span className="text-sm text-slate-500">Application #{appId}</span>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {!rec ? (
        <Alert type="warning">
          No recommendation available yet. Run the AI workflow to generate one.
        </Alert>
      ) : (
        <>
          {/* AI Recommendation hero */}
          <Card>
            <div className="flex flex-col sm:flex-row items-center gap-6">
              {/* Recommendation indicator */}
              <div className="text-center">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                  AI Recommendation
                </p>
                <RecommendationBadge rec={rec} size="lg" />
                <p className="text-xs text-slate-400 mt-2">
                  Confidence: {(confidence * 100).toFixed(0)}%
                </p>
              </div>

              {/* Short reason */}
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-700">{reason}</p>
                {citations.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {citations.map((c) => (
                      <span
                        key={c}
                        className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full font-medium"
                      >
                        {c}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Human gate reminder */}
            <div className="mt-4 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-800">
              ⚠️ <strong>This is an AI recommendation only.</strong> A licensed human underwriter
              must review and make the final APPROVE / REFER / DECLINE decision.
            </div>
          </Card>

          {/* Per-clause explanations — Req 3 */}
          {clauseReasons.length > 0 && (
            <Card title="Per-Clause Explanation">
              <div className="space-y-3">
                {clauseReasons.map((cr) => (
                  <div
                    key={cr.clause}
                    className={clsx(
                      'p-4 rounded-xl border',
                      cr.pass_fail === 'PASS'
                        ? 'bg-green-50 border-green-200'
                        : 'bg-red-50 border-red-200'
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">
                        {cr.clause}
                      </span>
                      <span
                        className={clsx(
                          'text-xs font-semibold px-2 py-0.5 rounded-full',
                          cr.pass_fail === 'PASS'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700'
                        )}
                      >
                        {cr.pass_fail}
                      </span>
                    </div>
                    <p className="text-sm font-semibold text-slate-800">{cr.criterion}</p>
                    <p className="text-xs text-slate-600 mt-1">{cr.rationale}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Policy score breakdown */}
          {scores && (scores as { criteria?: unknown }).criteria && (
            <Card title="Score Breakdown">
              <PolicyScoreTable scores={scores as Parameters<typeof PolicyScoreTable>[0]['scores']} />
            </Card>
          )}

          {/* Full AI explanation */}
          {explanation && (
            <Card title="Full AI Reasoning">
              <pre className="text-xs text-slate-600 whitespace-pre-wrap font-mono bg-slate-50 p-4 rounded-lg overflow-x-auto">
                {explanation}
              </pre>
            </Card>
          )}

          {/* Navigate to human decision */}
          <div className="flex justify-end">
            <Link
              to={`/human-review/${appId}`}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm rounded-lg"
            >
              👨‍⚖️ Proceed to Human Decision →
            </Link>
          </div>
        </>
      )}
    </div>
  )
}
