/**
 * Policy Score Breakdown Page — Requirement 2.
 *
 * Displays the transparent, clause-referenced policy scoring:
 *   Clause 3.1 — DTI (40%)
 *   Clause 3.2 — Credit History (30%)
 *   Clause 3.3 — Income Stability (20%)
 *   Clause 3.4 — Employment Stability (10%)
 *   Total: 100 pts
 */

import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getRecommendation, type ScoreBreakdown } from '../api/client'
import {
  Card,
  Alert,
  Spinner,
  PolicyScoreTable,
  ProgressBar,
} from '../components/ui'

export default function ScoringPage() {
  const { id } = useParams<{ id: string }>()
  const appId = Number(id)

  const [scores, setScores] = useState<ScoreBreakdown | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getRecommendation(appId)
      .then((r) => {
        if (r.score_breakdown) {
          setScores(r.score_breakdown)
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
        <h1 className="text-2xl font-bold text-slate-800">Policy Score Breakdown</h1>
        <span className="text-sm text-slate-500">Application #{appId}</span>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {!scores ? (
        <Alert type="warning">
          No scoring data yet. Run the AI workflow first to generate scores.
        </Alert>
      ) : (
        <>
          {/* Credit Policy reference header */}
          <Card>
            <div className="flex items-start gap-3">
              <span className="text-3xl">📊</span>
              <div>
                <h2 className="font-bold text-slate-800">Apex Credit Underwriting Policy</h2>
                <p className="text-sm text-slate-500 mt-0.5">
                  Every criterion is scored, weighted, and referenced to a policy clause.
                  The system is fully transparent — no unexplained scores.
                </p>
              </div>
            </div>
          </Card>

          {/* Clause-by-clause score cards */}
          <PolicyScoreTable scores={scores} />

          {/* Summary metrics */}
          <Card title="Score Summary">
            <div className="space-y-4">
              <ProgressBar
                value={scores.overall_risk_score}
                max={100}
                label="Overall Risk Score"
                color={
                  scores.overall_risk_score >= 75
                    ? 'green'
                    : scores.overall_risk_score >= 60
                    ? 'amber'
                    : 'red'
                }
              />
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-slate-500 text-xs">Credit Score (raw)</p>
                  <p className="font-bold text-slate-800 text-xl">
                    {scores.credit_score.toFixed(0)}/850
                  </p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-slate-500 text-xs">DTI Score</p>
                  <p className="font-bold text-slate-800 text-xl">
                    {scores.dti_score.toFixed(1)}%
                  </p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-slate-500 text-xs">Income Stability</p>
                  <p className="font-bold text-slate-800 text-xl">
                    {scores.income_stability_score.toFixed(1)}%
                  </p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-slate-500 text-xs">Employment Stability</p>
                  <p className="font-bold text-slate-800 text-xl">
                    {scores.employment_stability_score.toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Policy thresholds used */}
          {Object.keys(scores.policy_thresholds).length > 0 && (
            <Card title="Active Policy Thresholds (from database)">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="text-left py-2 text-slate-500">Rule Key</th>
                    <th className="text-right py-2 text-slate-500">Threshold Value</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(scores.policy_thresholds).map(([key, val]) => (
                    <tr key={key} className="border-b border-slate-50">
                      <td className="py-2 font-mono text-xs text-slate-600">{key}</td>
                      <td className="py-2 text-right font-semibold">{val}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
