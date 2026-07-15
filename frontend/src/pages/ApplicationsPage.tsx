/**
 * Applications List Page — shows all applications with status and links.
 */

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listApplications, processApplication, type Application } from '../api/client'
import { StatusBadge, Spinner, Alert, Card } from '../components/ui'
import { useAuth } from '../context/AuthContext'

export default function ApplicationsPage() {
  const { user } = useAuth()
  const [apps, setApps] = useState<Application[]>([])
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    listApplications()
      .then(setApps)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  async function handleProcess(appId: number) {
    setProcessing(appId)
    setError(null)
    setSuccess(null)
    try {
      const result = await processApplication(appId)
      setSuccess(`Application #${appId} processed. Status: ${result.final_status}`)
      // Refresh list
      const updated = await listApplications()
      setApps(updated)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Processing failed')
    } finally {
      setProcessing(null)
    }
  }

  const canProcess = user?.role === 'Underwriter' || user?.role === 'CreditManager'

  if (loading) return <div className="flex justify-center pt-20"><Spinner size="lg" /></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Applications</h1>
          <p className="text-slate-500 text-sm">{apps.length} total applications</p>
        </div>
        {user?.role === 'Applicant' && (
          <Link
            to="/upload"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg"
          >
            + New Application
          </Link>
        )}
      </div>

      {error && <Alert type="error">{error}</Alert>}
      {success && <Alert type="success">{success}</Alert>}

      <Card>
        {apps.length === 0 ? (
          <p className="text-slate-400 text-sm text-center py-8">
            No applications found.{' '}
            {user?.role === 'Applicant' && (
              <Link to="/upload" className="text-blue-600 hover:underline">
                Create one →
              </Link>
            )}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left">
                  <th className="py-3 px-3 text-slate-500 font-medium">ID</th>
                  <th className="py-3 px-3 text-slate-500 font-medium">Purpose</th>
                  <th className="py-3 px-3 text-right text-slate-500 font-medium">Amount</th>
                  <th className="py-3 px-3 text-right text-slate-500 font-medium">Term</th>
                  <th className="py-3 px-3 text-center text-slate-500 font-medium">Status</th>
                  <th className="py-3 px-3 text-right text-slate-500 font-medium">Created</th>
                  <th className="py-3 px-3 text-center text-slate-500 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {apps.map((app) => (
                  <tr key={app.id} className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="py-3 px-3">
                      <Link
                        to={`/applications/${app.id}`}
                        className="text-blue-600 hover:underline font-mono font-bold"
                      >
                        #{app.id}
                      </Link>
                    </td>
                    <td className="py-3 px-3 text-slate-700">{app.loan_purpose}</td>
                    <td className="py-3 px-3 text-right text-slate-700 font-medium">
                      ₹{app.loan_amount.toLocaleString()}
                    </td>
                    <td className="py-3 px-3 text-right text-slate-500">
                      {app.term_months}m
                    </td>
                    <td className="py-3 px-3 text-center">
                      <StatusBadge status={app.status} />
                    </td>
                    <td className="py-3 px-3 text-right text-xs text-slate-400">
                      {new Date(app.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-3 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <Link
                          to={`/applications/${app.id}`}
                          className="text-xs text-blue-600 hover:underline"
                        >
                          View
                        </Link>
                        {canProcess && app.status === 'SUBMITTED' && (
                          <button
                            onClick={() => handleProcess(app.id)}
                            disabled={processing === app.id}
                            className="text-xs px-2 py-1 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded"
                          >
                            {processing === app.id ? '⏳' : '▶ Process'}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
