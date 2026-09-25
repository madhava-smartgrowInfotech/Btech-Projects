import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { DashboardShell } from '@/components/layout/DashboardShell'
import { AuthProvider } from '@/context/AuthContext'
import { LandingPage } from '@/pages/LandingPage'
import { LoginPage } from '@/pages/LoginPage'
import { SignupPage } from '@/pages/SignupPage'

const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage').then((m) => ({ default: m.AnalyticsPage })))
const DashboardPage = lazy(() => import('@/pages/DashboardPage').then((m) => ({ default: m.DashboardPage })))
const DefectCatalogPage = lazy(() =>
  import('@/pages/DefectCatalogPage').then((m) => ({ default: m.DefectCatalogPage })),
)
const HistoryPage = lazy(() => import('@/pages/HistoryPage').then((m) => ({ default: m.HistoryPage })))
const InspectPage = lazy(() => import('@/pages/InspectPage').then((m) => ({ default: m.InspectPage })))
const InspectionDetailPage = lazy(() =>
  import('@/pages/InspectionDetailPage').then((m) => ({ default: m.InspectionDetailPage })),
)

function PageFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#05070c]">
      <div className="h-8 w-8 rounded-full border-2 border-cyan-400/30 border-t-cyan-400 animate-spin" />
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />

            <Route
              path="/app/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardShell>
                    <DashboardPage />
                  </DashboardShell>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/inspect"
              element={
                <ProtectedRoute>
                  <DashboardShell>
                    <InspectPage />
                  </DashboardShell>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/inspections/:id"
              element={
                <ProtectedRoute>
                  <DashboardShell>
                    <InspectionDetailPage />
                  </DashboardShell>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/history"
              element={
                <ProtectedRoute>
                  <DashboardShell>
                    <HistoryPage />
                  </DashboardShell>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/analytics"
              element={
                <ProtectedRoute>
                  <DashboardShell>
                    <AnalyticsPage />
                  </DashboardShell>
                </ProtectedRoute>
              }
            />
            <Route
              path="/app/catalog"
              element={
                <ProtectedRoute>
                  <DashboardShell>
                    <DefectCatalogPage />
                  </DashboardShell>
                </ProtectedRoute>
              }
            />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
