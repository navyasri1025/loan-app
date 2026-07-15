/**
 * API Client — typed fetch wrapper for the Apex Credit backend.
 *
 * Base URL is injected from the Vite environment variable VITE_API_URL.
 * All authenticated requests include the JWT token stored in localStorage.
 */

const BASE_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000'

// ─── Types ───────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface User {
  id: number
  email: string
  full_name: string
  role: string
  is_active: boolean
}

export interface Application {
  id: number
  applicant_id: number
  loan_amount: number
  loan_purpose: string
  term_months: number
  monthly_debt_obligations: number
  status: string
  created_at: string
  updated_at: string
}

export interface Document {
  id: number
  application_id: number
  document_type: string
  file_path: string
  status: string
  error_message?: string
}

export interface PolicyCriterion {
  name: string
  clause: string
  score: number
  max_score: number
  weight: number
  weighted_score: number
  max_weighted: number
  pass_fail: 'PASS' | 'FAIL'
  threshold_description: string
}

export interface ScoreBreakdown {
  dti_score: number
  income_stability_score: number
  employment_stability_score: number
  documentation_quality_score: number
  credit_score: number
  overall_risk_score: number
  policy_thresholds: Record<string, number>
  criteria: PolicyCriterion[]
  total_weighted_score: number
  max_total_weighted_score: number
}

export interface Recommendation {
  recommendation: 'APPROVE' | 'REFER' | 'DECLINE'
  confidence: number
  reason: string
  policy_citations: string[]
  explanation: string
  score_breakdown: ScoreBreakdown
}

export interface FairnessCheck {
  status: string
  original_recommendation: string
  identity_blind_recommendation?: string
  differences: string[]
  summary: string
}

export interface ValidationIssue {
  document_type: string
  issue_type: string
  severity: string
  message: string
}

export interface ValidationReport {
  status: 'PASS' | 'FAIL' | 'HOLD'
  issues: ValidationIssue[]
  valid_documents: string[]
  missing_documents: string[]
  summary: string
}

export interface WorkflowOutput {
  application_id: number
  final_status: string
  ai_recommendation?: Recommendation
  fairness_check?: FairnessCheck
  validation_report?: ValidationReport
  score_breakdown?: ScoreBreakdown
  audit_trail: unknown[]
  errors: string[]
}

export interface AuditLog {
  id: number
  action: string
  timestamp: string
  details: Record<string, unknown>
  hash: string
}

export interface EvaluationReport {
  total_applications_evaluated: number
  overall_score: number
  metrics: {
    trace_correctness: number
    tool_call_accuracy: number
    task_completion: number
    output_quality: number
    faithfulness: number
    fairness: number
    governance: number
  }
  summary: string
}

// ─── Auth helpers ─────────────────────────────────────────────────────────────

export function getToken(): string | null {
  return localStorage.getItem('apex_token')
}

export function setToken(token: string): void {
  localStorage.setItem('apex_token', token)
}

export function clearToken(): void {
  localStorage.removeItem('apex_token')
  localStorage.removeItem('apex_user')
}

export function getStoredUser(): User | null {
  const raw = localStorage.getItem('apex_user')
  return raw ? (JSON.parse(raw) as User) : null
}

// ─── Core fetch ───────────────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken()
  const headers: HeadersInit = {
    ...(options.headers ?? {}),
  }

  if (token) {
    ;(headers as Record<string, string>)['Authorization'] = `Bearer ${token}`
  }

  // Only set Content-Type for JSON bodies; multipart uses FormData
  if (!(options.body instanceof FormData)) {
    ;(headers as Record<string, string>)['Content-Type'] = 'application/json'
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(
      typeof errBody.detail === 'string'
        ? errBody.detail
        : JSON.stringify(errBody.detail) || res.statusText
    )
  }

  return res.json() as Promise<T>
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export async function login(email: string, password: string): Promise<TokenResponse> {
  // Backend LoginRequest schema expects JSON: { "email": "...", "password": "..." }
  const res = await fetch(`${BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Login failed' }))
    throw new Error(
      typeof err.detail === 'string' ? err.detail : (err.error ?? 'Login failed')
    )
  }
  const data: TokenResponse = await res.json()
  return data
}

export async function fetchCurrentUser(): Promise<User> {
  return apiFetch<User>('/api/auth/me')
}

// ─── Applications ─────────────────────────────────────────────────────────────

export async function listApplications(): Promise<Application[]> {
  return apiFetch<Application[]>('/api/applications/')
}

export async function getApplication(id: number): Promise<Application> {
  return apiFetch<Application>(`/api/applications/${id}`)
}

export async function createApplication(data: FormData): Promise<Application> {
  return apiFetch<Application>('/api/applications/', {
    method: 'POST',
    body: data,
  })
}

export async function uploadDocument(
  appId: number,
  documentType: string,
  file: File
): Promise<Document> {
  const fd = new FormData()
  fd.append('document_type', documentType)
  fd.append('file', file)
  return apiFetch<Document>(`/api/applications/${appId}/documents`, {
    method: 'POST',
    body: fd,
  })
}

export async function getDocuments(appId: number): Promise<Document[]> {
  return apiFetch<Document[]>(`/api/applications/${appId}/documents`)
}

// ─── Processing / Workflow ────────────────────────────────────────────────────

export async function processApplication(appId: number): Promise<WorkflowOutput> {
  return apiFetch<WorkflowOutput>(`/api/applications/${appId}/process`, {
    method: 'POST',
  })
}

export async function getWorkflowStatus(appId: number) {
  return apiFetch<{
    application_id: number
    status: string
    current_stage: string
    created_at: string
    updated_at: string
  }>(`/api/applications/${appId}/workflow-status`)
}

export async function submitHumanReview(
  appId: number,
  decision: 'APPROVE' | 'REFER' | 'DECLINE',
  comment?: string
) {
  const params = new URLSearchParams({ decision })
  if (comment) params.set('comment', comment)
  return apiFetch<{
    application_id: number
    decision: string
    status: string
    reviewed_at: string
    reviewer: string
  }>(`/api/applications/${appId}/human-review?${params.toString()}`, {
    method: 'POST',
  })
}

export async function getRecommendation(appId: number) {
  return apiFetch<{
    application_id: number
    recommendation?: string
    confidence?: number
    reason?: string
    score_breakdown?: ScoreBreakdown
    policy_citations?: string[]
    fairness_status?: string
    fairness_summary?: string
    full_details?: Record<string, unknown>
  }>(`/api/applications/${appId}/recommendation`)
}

export async function getAuditTrail(
  appId: number
): Promise<{ application_id: number; audit_logs: AuditLog[]; total_entries: number }> {
  return apiFetch(`/api/applications/${appId}/audit-trail`)
}

// ─── Demo Scenarios ──────────────────────────────────────────────────────────

export async function runScenario1() {
  return apiFetch('/api/demo/scenario/1/strong-application', { method: 'POST' })
}

export async function runScenario2() {
  return apiFetch('/api/demo/scenario/2/borderline-application', { method: 'POST' })
}

export async function runScenario3() {
  return apiFetch('/api/demo/scenario/3/missing-documents', { method: 'POST' })
}

export async function runScenario4() {
  return apiFetch('/api/demo/scenario/4/identity-consistency', { method: 'POST' })
}

export async function runScenario5() {
  return apiFetch('/api/demo/scenario/5/prompt-injection', { method: 'POST' })
}

export async function listScenarios() {
  return apiFetch('/api/demo/scenarios/list')
}

// ─── Evaluation ───────────────────────────────────────────────────────────────

export async function getEvaluationReport(): Promise<EvaluationReport> {
  return apiFetch<EvaluationReport>('/api/evaluation/report')
}

// ─── Audit Logs (general) ─────────────────────────────────────────────────────

export async function getReports() {
  return apiFetch('/api/reports/')
}
