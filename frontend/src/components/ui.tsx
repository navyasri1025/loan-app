/**
 * Shared UI Components — reusable building blocks used across all pages.
 *
 * Exports:
 *   Badge, Card, StatCard, StatusBadge, ClauseCard, PolicyScoreTable,
 *   Spinner, Alert, ProgressBar, RecommendationBadge, FairnessResult
 */

import type { ReactNode } from 'react'
import * as React from 'react'
import { clsx } from 'clsx'
import type { PolicyCriterion, ScoreBreakdown } from '../api/client'

// ─── Badge ────────────────────────────────────────────────────────────────────

type BadgeVariant = 'blue' | 'green' | 'amber' | 'red' | 'gray' | 'indigo'

export function Badge({
  children,
  variant = 'gray',
}: {
  children: ReactNode
  variant?: BadgeVariant
}) {
  const cls: Record<BadgeVariant, string> = {
    blue: 'bg-blue-100 text-blue-800',
    green: 'bg-green-100 text-green-800',
    amber: 'bg-amber-100 text-amber-800',
    red: 'bg-red-100 text-red-800',
    gray: 'bg-gray-100 text-gray-700',
    indigo: 'bg-indigo-100 text-indigo-800',
  }
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold',
        cls[variant]
      )}
    >
      {children}
    </span>
  )
}

// ─── Card ─────────────────────────────────────────────────────────────────────

export function Card({
  children,
  className = '',
  title,
}: {
  children: ReactNode
  className?: string
  title?: string
}) {
  return (
    <div
      className={clsx(
        'bg-white rounded-2xl shadow-sm border border-slate-200 p-6',
        className
      )}
    >
      {title && (
        <h3 className="text-base font-semibold text-slate-800 mb-4">{title}</h3>
      )}
      {children}
    </div>
  )
}

// ─── StatCard ─────────────────────────────────────────────────────────────────

export function StatCard({
  label,
  value,
  sub,
  color = 'blue',
}: {
  label: string
  value: string | number
  sub?: string
  color?: 'blue' | 'green' | 'amber' | 'red' | 'purple'
}) {
  const accent: Record<string, string> = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    amber: 'text-amber-600',
    red: 'text-red-600',
    purple: 'text-purple-600',
  }
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
        {label}
      </p>
      <p className={clsx('mt-1 text-3xl font-bold', accent[color])}>{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
    </div>
  )
}

// ─── StatusBadge ─────────────────────────────────────────────────────────────

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeVariant> = {
    APPROVED: 'green',
    APPROVE: 'green',
    PASS: 'green',
    REFER: 'amber',
    REFER_TO_UNDERWRITER: 'amber',
    PENDING_REVIEW: 'amber',
    IN_REVIEW: 'amber',
    HOLD: 'amber',
    DECLINED: 'red',
    DECLINE: 'red',
    FAIL: 'red',
    FAIRNESS_FAILURE: 'red',
    DRAFT: 'gray',
    SUBMITTED: 'blue',
    FAILED: 'red',
  }
  return <Badge variant={map[status] ?? 'gray'}>{status}</Badge>
}

// ─── Spinner ─────────────────────────────────────────────────────────────────

export function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizes = { sm: 'h-4 w-4', md: 'h-8 w-8', lg: 'h-12 w-12' }
  return (
    <div className="flex justify-center items-center">
      <div
        className={clsx(
          'animate-spin rounded-full border-2 border-slate-200 border-t-blue-600',
          sizes[size]
        )}
      />
    </div>
  )
}

// ─── Alert ───────────────────────────────────────────────────────────────────

type AlertType = 'info' | 'success' | 'warning' | 'error'

export function Alert({
  type = 'info',
  children,
}: {
  type?: AlertType
  children: ReactNode
}) {
  const styles: Record<AlertType, string> = {
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    success: 'bg-green-50 border-green-200 text-green-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    error: 'bg-red-50 border-red-200 text-red-800',
  }
  return (
    <div
      className={clsx(
        'border rounded-xl px-4 py-3 text-sm font-medium',
        styles[type]
      )}
    >
      {children}
    </div>
  )
}

// ─── ProgressBar ─────────────────────────────────────────────────────────────

export function ProgressBar({
  value,
  max = 100,
  color = 'blue',
  label,
}: {
  value: number
  max?: number
  color?: 'blue' | 'green' | 'amber' | 'red'
  label?: string
}) {
  const pct = Math.min(100, (value / max) * 100)
  const bars: Record<string, string> = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    amber: 'bg-amber-500',
    red: 'bg-red-500',
  }
  return (
    <div>
      {label && (
        <div className="flex justify-between text-xs text-slate-500 mb-1">
          <span>{label}</span>
          <span>
            {value.toFixed(1)} / {max}
          </span>
        </div>
      )}
      <div className="w-full bg-slate-100 rounded-full h-2.5">
        <div
          className={clsx('h-2.5 rounded-full transition-all', bars[color])}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

// ─── RecommendationBadge ─────────────────────────────────────────────────────

export function RecommendationBadge({
  rec,
  size = 'md',
}: {
  rec: string
  size?: 'sm' | 'md' | 'lg'
}) {
  const colors: Record<string, string> = {
    APPROVE: 'bg-green-500',
    REFER: 'bg-amber-500',
    DECLINE: 'bg-red-500',
  }
  const sizes = {
    sm: 'text-xs px-2.5 py-1',
    md: 'text-sm px-4 py-1.5',
    lg: 'text-base px-6 py-2.5',
  }
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full font-bold text-white',
        colors[rec] ?? 'bg-gray-400',
        sizes[size]
      )}
    >
      {rec}
    </span>
  )
}

// ─── ClauseCard — shows one policy criterion ─────────────────────────────────

export function ClauseCard({ c }: { c: PolicyCriterion }) {
  const passBg = c.pass_fail === 'PASS' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
  const passText = c.pass_fail === 'PASS' ? 'text-green-700' : 'text-red-700'
  const barColor: 'green' | 'red' = c.pass_fail === 'PASS' ? 'green' : 'red'

  return (
    <div className={clsx('rounded-xl border p-4 space-y-3', passBg)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            {c.clause}
          </span>
          <h4 className="text-sm font-semibold text-slate-800">{c.name}</h4>
        </div>
        <span
          className={clsx(
            'text-xs font-bold px-2 py-0.5 rounded-full',
            c.pass_fail === 'PASS'
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          )}
        >
          {c.pass_fail}
        </span>
      </div>

      {/* Score bar */}
      <ProgressBar
        value={c.score}
        max={c.max_score}
        color={barColor}
        label={`Score: ${c.score.toFixed(1)} / ${c.max_score.toFixed(0)}`}
      />

      {/* Metrics row */}
      <div className="grid grid-cols-3 gap-2 text-center text-xs">
        <div className="bg-white/60 rounded-lg py-1.5">
          <p className="text-slate-500">Weight</p>
          <p className="font-semibold text-slate-700">{(c.weight * 100).toFixed(0)}%</p>
        </div>
        <div className="bg-white/60 rounded-lg py-1.5">
          <p className="text-slate-500">Weighted Score</p>
          <p className={clsx('font-semibold', passText)}>
            {c.weighted_score.toFixed(1)} / {c.max_weighted.toFixed(0)}
          </p>
        </div>
        <div className="bg-white/60 rounded-lg py-1.5">
          <p className="text-slate-500">Policy</p>
          <p className="font-semibold text-slate-700">{c.clause}</p>
        </div>
      </div>

      <p className="text-xs text-slate-500">📋 {c.threshold_description}</p>
    </div>
  )
}

// ─── PolicyScoreTable — full score breakdown ──────────────────────────────────

export function PolicyScoreTable({ scores }: { scores: ScoreBreakdown }) {
  const total = scores.total_weighted_score ?? scores.overall_risk_score
  const max = scores.max_total_weighted_score ?? 100

  return (
    <div className="space-y-4">
      {/* Per-clause cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {scores.criteria && scores.criteria.length > 0
          ? scores.criteria.map((c) => <ClauseCard key={c.clause} c={c} />)
          : null}
      </div>

      {/* Total */}
      <div className="bg-slate-800 text-white rounded-xl p-4 flex items-center justify-between">
        <span className="font-semibold">Total Score</span>
        <div className="text-right">
          <span className="text-2xl font-bold">
            {total.toFixed(1)} / {max.toFixed(0)}
          </span>
          <span className="ml-2 text-sm text-slate-300">
            ({((total / max) * 100).toFixed(1)}%)
          </span>
        </div>
      </div>
    </div>
  )
}

// ─── FairnessResult ───────────────────────────────────────────────────────────

export function FairnessResult({
  status,
  original,
  blind,
  summary,
}: {
  status: string
  original: string
  blind?: string
  summary: string
}) {
  const passed = status === 'PASS'
  return (
    <div
      className={clsx(
        'rounded-xl border p-5 space-y-4',
        passed ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
      )}
    >
      <div className="flex items-center gap-3">
        <span className="text-2xl">{passed ? '✅' : '⚠️'}</span>
        <div>
          <p className="font-bold text-slate-800">
            Fairness Check: {passed ? 'PASSED' : 'FAILED'}
          </p>
          <p className="text-xs text-slate-500">{summary}</p>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white/60 rounded-lg p-3 text-center">
          <p className="text-xs text-slate-500 mb-1">Original Recommendation</p>
          <RecommendationBadge rec={original} size="sm" />
        </div>
        <div className="bg-white/60 rounded-lg p-3 text-center">
          <p className="text-xs text-slate-500 mb-1">Identity-Blind Recommendation</p>
          {blind ? <RecommendationBadge rec={blind} size="sm" /> : <span className="text-xs text-slate-400">—</span>}
        </div>
      </div>
    </div>
  )
}

// ─── WorkflowProgressBar ─────────────────────────────────────────────────────

const STAGES = [
  'Intake',
  'OCR',
  'Validation',
  'Scoring',
  'Recommendation',
  'Fairness',
  'Governance',
  'Human Review',
]

export function WorkflowProgress({ currentStage }: { currentStage: number }): React.JSX.Element {
  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-2">
      {STAGES.map((stage, i) => (
        <div key={stage} className="flex items-center gap-1">
          <div className="flex flex-col items-center">
            <div
              className={clsx(
                'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors',
                i < currentStage
                  ? 'bg-green-500 text-white'
                  : i === currentStage
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-200 text-slate-500'
              )}
            >
              {i < currentStage ? '✓' : i + 1}
            </div>
            <span className="text-[10px] text-slate-500 mt-0.5 whitespace-nowrap">
              {stage}
            </span>
          </div>
          {i < STAGES.length - 1 && (
            <div
              className={clsx(
                'h-0.5 w-8 mb-3 rounded',
                i < currentStage ? 'bg-green-400' : 'bg-slate-200'
              )}
            />
          )}
        </div>
      ))}
    </div>
  )
}
