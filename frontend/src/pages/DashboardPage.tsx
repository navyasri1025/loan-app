/**
 * Dashboard Page — overview of applications, AI metrics, and system health.
 */

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  listApplications,
  getEvaluationReport,
  type Application,
  type EvaluationReport,
} from '../api/client'
import { StatCard, Card, StatusBadge, Spinner, Alert } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts'

export default function DashboardPage() {
  const { user } = useAuth()
  const [apps, setApps] = useState<Application[]>([])
  const [report, setReport] = useState<EvaluationReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([listApplications(), getEvaluationReport()])
      .then(([a, r]) => {
        setApps(a)
        setReport(r)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>
  if (error) return <Alert type="error">{error}</Alert>

  // Derive counts
  const counts = {
    total: apps.length,
    approved: apps.filter((a) => a.status === 'APPROVED').length,
    pending: apps.filter((a) => ['PENDING_REVIEW', 'IN_REVIEW', 'SUBMITTED'].includes(a.status)).length,
    declined: apps.filter((a) => a.status === 'DECLINED').length,
    hold: apps.filter((a) => a.status === 'HOLD').length,
  }

  // Recent applications (last 5)
  const recent = [...apps]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 5)

  // Radar data
  const radarData = report
    ? Object.entries(report.metrics).map(([key, val]) => ({
        metric: key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
        value: val,
      }))
    : []

  // Bar data for status distribution
  const barData = [
    { name: 'Approved', value: counts.approved, fill: '#16a34a' },
    { name: 'Pending', value: counts.pending, fill: '#d97706' },
    { name: 'Declined', value: counts.declined, fill: '#dc2626' },
    { name: 'Hold', value: counts.hold, fill: '#7c3aed' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
          <p className="text-slate-500 text-sm">
            Welcome back, {user?.full_name} • {user?.role}
          </p>
        </div>
        <Link
          to="/demo"
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          🧪 Run Demo Scenarios
        </Link>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Applications" value={counts.total} color="blue" />
        <StatCard label="Approved" value={counts.approved} color="green" />
        <StatCard label="Pending Review" value={counts.pending} color="amber" />
        <StatCard label="Declined" value={counts.declined} color="red" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status distribution bar chart */}
        <Card title="Application Status Distribution">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={barData}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
              <Tooltip />
              {barData.map((entry) => (
                <Bar key={entry.name} dataKey="value" fill={entry.fill} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* AI Evaluation radar */}
        {report && (
          <Card title={`AI System Evaluation — Overall ${report.overall_score.toFixed(1)}%`}>
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10 }} />
                <Radar
                  name="Score"
                  dataKey="value"
                  stroke="#2563eb"
                  fill="#2563eb"
                  fillOpacity={0.25}
                />
              </RadarChart>
            </ResponsiveContainer>
            <p className="text-xs text-slate-500 mt-2 text-center">{report.summary}</p>
          </Card>
        )}
      </div>

      {/* Recent applications */}
      <Card title="Recent Applications">
        {recent.length === 0 ? (
          <p className="text-slate-400 text-sm">No applications yet. Submit one to get started.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left py-2 px-2 text-slate-500 font-medium">ID</th>
                  <th className="text-left py-2 px-2 text-slate-500 font-medium">Purpose</th>
                  <th className="text-right py-2 px-2 text-slate-500 font-medium">Amount</th>
                  <th className="text-center py-2 px-2 text-slate-500 font-medium">Status</th>
                  <th className="text-right py-2 px-2 text-slate-500 font-medium">Updated</th>
                </tr>
              </thead>
              <tbody>
                {recent.map((app) => (
                  <tr key={app.id} className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="py-2 px-2">
                      <Link
                        to={`/applications/${app.id}`}
                        className="text-blue-600 hover:underline font-mono text-xs"
                      >
                        #{app.id}
                      </Link>
                    </td>
                    <td className="py-2 px-2 text-slate-700">{app.loan_purpose}</td>
                    <td className="py-2 px-2 text-right text-slate-700">
                      ₹{app.loan_amount.toLocaleString()}
                    </td>
                    <td className="py-2 px-2 text-center">
                      <StatusBadge status={app.status} />
                    </td>
                    <td className="py-2 px-2 text-right text-xs text-slate-400">
                      {new Date(app.updated_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="mt-3 text-right">
          <Link to="/applications" className="text-xs text-blue-600 hover:underline">
            View all applications →
          </Link>
        </div>
      </Card>
    </div>
  )
}
