/**
 * Fairness Check Page — Requirement 5.
 *
 * Shows:
 *   • Original recommendation
 *   • Identity-blind recommendation
 *   • Pass / Fail result
 *   • Differences (if any)
 *   • Summary
 */

import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getRecommendation } from '../api/client'
import {
  Card,
  Alert,
  Spinner,
  FairnessResult,
  RecommendationBadge,
} from '../components/ui'

export default function FairnessPage() {
  const { id } = useParams<{ id: string }>()
  const appId = Number(id)

  const [fairness, setFairness] = useState<{
    status: string
    original_recommendation: string
    identity_blind_recommendation?: string
    differences?: string[]
    summary: string
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getRecommendation(appId)
      .then((r) => {
        const details = r.full_details as Record<string, unknown> | undefined
        const fc = details?.fairness_check as typeof fairness | undefined
        if (fc) {
          setFairness(fc)
        } else if (r.fairness_status) {
          setFairness({
            status: r.fairness_status,
            original_recommendation: r.recommendation ?? '',
            summary: r.fairness_summary ?? '',
          })
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [appId])

  if (loading) return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-3">
        <Link to={`/applications/${appId}`} className="text-blue-600 text-sm hover:underline">← Back</Link>
        <h1 className="text-2xl font-bold text-slate-800">Fairness Check</h1>
        <span className="text-sm text-slate-500">Application #{appId}</span>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {/* How fairness works */}
      <Card title="How the Fairness Agent Works (Req 5)">
        <div className="space-y-2 text-sm text-slate-600">
          {[
            { icon: '1️⃣', text: 'Run original scoring with full applicant data' },
            { icon: '2️⃣', text: 'Remove identity fields (name, address, phone, email, gender, date_of_birth)' },
            { icon: '3️⃣', text: 'Re-run scoring on identity-blind data' },
            { icon: '4️⃣', text: 'Compare both recommendations' },
            {
              icon: '✅',
              text: 'If recommendations match → PASS (no identity-based bias detected)',
            },
            {
              icon: '❌',
              text: 'If recommendations differ → FAIL (potential bias flagged in audit log)',
            },
          ].map((item, i) => (
            <div key={i} className="flex items-start gap-2">
              <span>{item.icon}</span>
              <span>{item.text}</span>
            </div>
          ))}
        </div>
      </Card>

      {!fairness ? (
        <Alert type="warning">
          No fairness data yet. Run the AI workflow to generate the fairness check.
        </Alert>
      ) : (
        <>
          {/* Fairness result card */}
          <FairnessResult
            status={fairness.status}
            original={fairness.original_recommendation}
            blind={fairness.identity_blind_recommendation}
            summary={fairness.summary}
          />

          {/* Comparison detail */}
          <Card title="Comparison Details">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-50 rounded-xl p-4 text-center">
                <p className="text-xs text-slate-500 mb-2">With Identity</p>
                <RecommendationBadge rec={fairness.original_recommendation} />
                <p className="text-xs text-slate-400 mt-2">
                  Full applicant profile (name, address, etc. included)
                </p>
              </div>
              <div className="bg-slate-50 rounded-xl p-4 text-center">
                <p className="text-xs text-slate-500 mb-2">Identity Blind</p>
                {fairness.identity_blind_recommendation ? (
                  <RecommendationBadge rec={fairness.identity_blind_recommendation} />
                ) : (
                  <RecommendationBadge rec={fairness.original_recommendation} />
                )}
                <p className="text-xs text-slate-400 mt-2">
                  Name, address, phone, email, gender removed
                </p>
              </div>
            </div>
          </Card>

          {/* Differences */}
          {(fairness.differences?.length ?? 0) > 0 && (
            <Card title="Detected Differences">
              <ul className="space-y-2">
                {fairness.differences?.map((d, i) => (
                  <li key={i} className="text-sm text-red-700 bg-red-50 rounded-lg px-3 py-2">
                    ⚠️ {d}
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
