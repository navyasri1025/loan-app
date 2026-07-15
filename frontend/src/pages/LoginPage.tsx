/**
 * Login Page — JWT authentication form.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Alert, Spinner } from '../components/ui'

// Demo credential hints
const DEMO_USERS = [
  { role: 'Applicant',      email: 'applicant@demo.com',   password: 'Password123@' },
  { role: 'Underwriter',    email: 'underwriter@demo.com', password: 'Password123@' },
  { role: 'Credit Manager', email: 'manager@demo.com',     password: 'Password123@' },
  { role: 'Auditor',        email: 'auditor@demo.com',     password: 'Password123@' },
]

export default function LoginPage() {
  const { login, isLoading } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    }
  }

  function fillDemo(u: (typeof DEMO_USERS)[0]) {
    setEmail(u.email)
    setPassword(u.password)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-blue-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <span className="text-5xl">🏦</span>
            <h1 className="mt-3 text-2xl font-bold text-slate-800">Apex Credit</h1>
            <p className="text-slate-500 text-sm mt-1">AI-Powered Loan Processing Platform</p>
          </div>

          {/* Error */}
          {error && <Alert type="error">{error}</Alert>}

          {/* Form */}
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="••••••••"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold rounded-lg transition-colors"
            >
              {isLoading ? <Spinner size="sm" /> : 'Sign In'}
            </button>
          </form>

          {/* Demo credentials */}
          <div className="mt-6 border-t pt-4">
            <p className="text-xs text-slate-400 mb-2 text-center font-medium uppercase tracking-wide">
              Demo Accounts
            </p>
            <div className="grid grid-cols-2 gap-2">
              {DEMO_USERS.map((u) => (
                <button
                  key={u.email}
                  onClick={() => fillDemo(u)}
                  className="text-xs text-left px-3 py-2 rounded-lg bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-200 transition-colors"
                >
                  <span className="font-semibold text-blue-600">{u.role}</span>
                  <br />
                  <span className="text-slate-400">{u.email}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
