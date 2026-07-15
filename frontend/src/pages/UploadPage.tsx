/**
 * Application Upload Page — create a new loan application and upload documents.
 *
 * Req 1: Government ID, Income Proof, Bank Statement required.
 * Shows which documents are mandatory.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createApplication, uploadDocument } from '../api/client'
import { Alert, Card, Spinner, WorkflowProgress } from '../components/ui'

const REQUIRED_DOCS = [
  { type: 'PAN',             label: 'PAN Card',              group: 'Government ID', required: true },
  { type: 'Aadhaar',         label: 'Aadhaar Card',          group: 'Government ID', required: true },
  { type: 'Salary Slip',     label: 'Salary Slip (3 months)', group: 'Income Proof', required: true },
  { type: 'Employment Letter', label: 'Employment Letter',   group: 'Income Proof',  required: false },
  { type: 'Bank Statement',  label: 'Bank Statement (6 months)', group: 'Bank Statement', required: true },
]

export default function UploadPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState<1 | 2>(1)
  const [appId, setAppId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Step 1: Application form state
  const [form, setForm] = useState({
    loan_amount: '',
    loan_purpose: '',
    term_months: '36',
    monthly_debt_obligations: '0',
    monthly_income: '',
    employer_name: '',
    employment_type: 'Salaried',
    employment_stability_months: '12',
    phone: '',
    date_of_birth: '',
    address: '',
    gender: '',
  })

  // Step 2: File uploads state
  const [files, setFiles] = useState<Record<string, File | null>>({})
  const [uploaded, setUploaded] = useState<Record<string, boolean>>({})

  // ── Step 1: Create application ────────────────────────────────────────────

  async function handleCreateApplication(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const fd = new FormData()
      Object.entries(form).forEach(([k, v]) => fd.append(k, v))
      const app = await createApplication(fd)
      setAppId(app.id)
      setStep(2)
      setSuccess(`Application #${app.id} created. Now upload your documents.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create application')
    } finally {
      setLoading(false)
    }
  }

  // ── Step 2: Upload documents ──────────────────────────────────────────────

  async function handleUpload(docType: string) {
    const file = files[docType]
    if (!file || !appId) return
    setLoading(true)
    setError(null)
    try {
      await uploadDocument(appId, docType, file)
      setUploaded((prev) => ({ ...prev, [docType]: true }))
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to upload ${docType}`)
    } finally {
      setLoading(false)
    }
  }

  async function handleProcess() {
    if (!appId) return
    navigate(`/applications/${appId}`)
  }

  const allRequiredUploaded = REQUIRED_DOCS.filter((d) => d.required).every(
    (d) => uploaded[d.type]
  )

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">New Loan Application</h1>
        <p className="text-slate-500 text-sm mt-1">
          Complete the form and upload all required documents.
        </p>
      </div>

      {/* Progress bar */}
      <WorkflowProgress currentStage={step === 1 ? 0 : 1} />

      {error && <Alert type="error">{error}</Alert>}
      {success && <Alert type="success">{success}</Alert>}

      {/* ── Step 1: Application form ──────────────────────────────────────── */}
      {step === 1 && (
        <Card title="Loan Details">
          <form onSubmit={handleCreateApplication} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-slate-600">Loan Amount (₹)</label>
                <input
                  type="number"
                  required
                  value={form.loan_amount}
                  onChange={(e) => setForm({ ...form, loan_amount: e.target.value })}
                  className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Loan Purpose</label>
                <input
                  type="text"
                  required
                  value={form.loan_purpose}
                  onChange={(e) => setForm({ ...form, loan_purpose: e.target.value })}
                  placeholder="Home Purchase, Education, etc."
                  className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Term (months)</label>
                <input
                  type="number"
                  required
                  value={form.term_months}
                  onChange={(e) => setForm({ ...form, term_months: e.target.value })}
                  className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Monthly Debt Obligations (₹)</label>
                <input
                  type="number"
                  value={form.monthly_debt_obligations}
                  onChange={(e) => setForm({ ...form, monthly_debt_obligations: e.target.value })}
                  className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Monthly Income (₹)</label>
                <input
                  type="number"
                  required
                  value={form.monthly_income}
                  onChange={(e) => setForm({ ...form, monthly_income: e.target.value })}
                  className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Employer Name</label>
                <input
                  type="text"
                  value={form.employer_name}
                  onChange={(e) => setForm({ ...form, employer_name: e.target.value })}
                  className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Employment Type</label>
                <select
                  value={form.employment_type}
                  onChange={(e) => setForm({ ...form, employment_type: e.target.value })}
                  className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option>Salaried</option>
                  <option>Self-Employed</option>
                  <option>Unemployed</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Employment Stability (months)</label>
                <input
                  type="number"
                  value={form.employment_stability_months}
                  onChange={(e) => setForm({ ...form, employment_stability_months: e.target.value })}
                  className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Phone</label>
                <input
                  type="text"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Date of Birth</label>
                <input
                  type="date"
                  value={form.date_of_birth}
                  onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })}
                  className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600">Address</label>
              <input
                type="text"
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
                className="mt-1 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-semibold rounded-lg"
            >
              {loading ? <Spinner size="sm" /> : 'Continue to Document Upload →'}
            </button>
          </form>
        </Card>
      )}

      {/* ── Step 2: Document upload ───────────────────────────────────────── */}
      {step === 2 && appId && (
        <Card title="Document Upload">
          <p className="text-sm text-slate-500 mb-4">
            ⚠️ Documents marked <span className="font-semibold text-red-600">*Required</span> must be
            uploaded before the AI can process your application.
          </p>

          <div className="space-y-3">
            {REQUIRED_DOCS.map((doc) => (
              <div
                key={doc.type}
                className="flex items-center gap-3 p-3 border border-slate-200 rounded-lg bg-slate-50"
              >
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-700">
                    {doc.label}
                    {doc.required && (
                      <span className="ml-1 text-red-600 text-xs">*Required</span>
                    )}
                  </p>
                  <p className="text-xs text-slate-400">Group: {doc.group}</p>
                </div>

                {uploaded[doc.type] ? (
                  <span className="text-green-600 text-sm font-medium">✅ Uploaded</span>
                ) : (
                  <div className="flex items-center gap-2">
                    <input
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png"
                      onChange={(e) =>
                        setFiles({ ...files, [doc.type]: e.target.files?.[0] ?? null })
                      }
                      className="text-xs text-slate-500"
                    />
                    <button
                      onClick={() => handleUpload(doc.type)}
                      disabled={!files[doc.type] || loading}
                      className="px-3 py-1.5 text-xs bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg"
                    >
                      Upload
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="mt-6 flex gap-3">
            <button
              onClick={handleProcess}
              disabled={!allRequiredUploaded || loading}
              className="flex-1 py-2.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-semibold rounded-lg"
            >
              {loading ? <Spinner size="sm" /> : '✅ View Application →'}
            </button>
          </div>

          {!allRequiredUploaded && (
            <Alert type="warning">
              Please upload all required documents before proceeding.
            </Alert>
          )}
        </Card>
      )}
    </div>
  )
}
