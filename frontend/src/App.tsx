/**
 * App.tsx — Root component.
 *
 * Sets up:
 *   - React Router with all pages
 *   - AuthProvider context
 *   - Protected route guard
 *   - Layout shell
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'

// Pages
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ApplicationsPage from './pages/ApplicationsPage'
import ApplicationDetailPage from './pages/ApplicationDetailPage'
import UploadPage from './pages/UploadPage'
import ValidationPage from './pages/ValidationPage'
import ScoringPage from './pages/ScoringPage'
import RecommendationPage from './pages/RecommendationPage'
import FairnessPage from './pages/FairnessPage'
import HumanReviewPage from './pages/HumanReviewPage'
import AuditPage from './pages/AuditPage'
import DemoPage from './pages/DemoPage'

// ── Protected Route guard ─────────────────────────────────────────────────────

function Protected({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  if (isLoading) return null
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

// ── App Routes ────────────────────────────────────────────────────────────────

function AppRoutes() {
  const { isAuthenticated } = useAuth()

  return (
    <Routes>
      {/* Public */}
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />}
      />

      {/* Protected routes */}
      <Route path="/dashboard" element={<Protected><DashboardPage /></Protected>} />
      <Route path="/applications" element={<Protected><ApplicationsPage /></Protected>} />
      <Route path="/applications/:id" element={<Protected><ApplicationDetailPage /></Protected>} />
      <Route path="/upload" element={<Protected><UploadPage /></Protected>} />

      {/* Workflow detail pages — accept optional :id param */}
      <Route path="/validation/:id" element={<Protected><ValidationPage /></Protected>} />
      <Route path="/scoring/:id" element={<Protected><ScoringPage /></Protected>} />
      <Route path="/recommendation/:id" element={<Protected><RecommendationPage /></Protected>} />
      <Route path="/fairness/:id" element={<Protected><FairnessPage /></Protected>} />
      <Route path="/human-review/:id" element={<Protected><HumanReviewPage /></Protected>} />
      <Route path="/audit/:id" element={<Protected><AuditPage /></Protected>} />

      {/* Without ID — show instructions */}
      <Route path="/validation" element={<Protected><ValidationPage /></Protected>} />
      <Route path="/scoring" element={<Protected><ScoringPage /></Protected>} />
      <Route path="/recommendation" element={<Protected><RecommendationPage /></Protected>} />
      <Route path="/fairness" element={<Protected><FairnessPage /></Protected>} />
      <Route path="/human-review" element={<Protected><HumanReviewPage /></Protected>} />
      <Route path="/audit" element={<Protected><AuditPage /></Protected>} />

      {/* Demo */}
      <Route path="/demo" element={<Protected><DemoPage /></Protected>} />

      {/* Default redirects */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

// ── Root export ───────────────────────────────────────────────────────────────

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
