import { lazy, Suspense, useEffect } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { AppShell, PublicShell, SkeletonBlock, Container } from './components/ui'
import { PageTransition } from './components/motion'
import { useAuth } from './lib/auth'

const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const Catalog = lazy(() => import('./pages/Catalog'))
const CourseDetail = lazy(() => import('./pages/CourseDetail'))
const Analytics = lazy(() => import('./pages/Analytics'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Recommendations = lazy(() => import('./pages/Recommendations'))
const LearningPath = lazy(() => import('./pages/LearningPath'))
const Insights = lazy(() => import('./pages/Insights'))
const Activity = lazy(() => import('./pages/Activity'))
const Profile = lazy(() => import('./pages/Profile'))
const NotFound = lazy(() => import('./pages/NotFound'))

function PageFallback() {
  return (
    <Container style={{ paddingTop: 40 }}>
      <SkeletonBlock rows={4} label="Loading page" />
    </Container>
  )
}

/** Scroll to top and reset focus target on navigation. */
function RouteEffects() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

function Page() {
  const { pathname } = useLocation()
  return (
    <Suspense fallback={<PageFallback />}>
      <PageTransition key={pathname}>
        <Outlet />
      </PageTransition>
    </Suspense>
  )
}

function PublicLayout() {
  return (
    <PublicShell>
      <Page />
    </PublicShell>
  )
}

/** Signed-in learners get the app shell; signed-out visitors get the public one. */
function AdaptiveLayout() {
  const { user, loading } = useAuth()
  if (loading) return <PageFallback />
  const Shell = user ? AppShell : PublicShell
  return (
    <Shell>
      <Page />
    </Shell>
  )
}

function RequireAuth() {
  const { user, loading } = useAuth()
  const loc = useLocation()
  if (loading) return <PageFallback />
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname + loc.search }} />
  return (
    <AppShell>
      <Page />
    </AppShell>
  )
}

export default function App() {
  return (
    <>
      <RouteEffects />
      <Routes>
        <Route element={<PublicLayout />}>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Route>
        <Route element={<AdaptiveLayout />}>
          <Route path="/courses" element={<Catalog />} />
          <Route path="/courses/:id" element={<CourseDetail />} />
          <Route path="/analytics" element={<Analytics />} />
        </Route>
        <Route path="/app" element={<RequireAuth />}>
          <Route index element={<Dashboard />} />
          <Route path="recommendations" element={<Recommendations />} />
          <Route path="path" element={<LearningPath />} />
          <Route path="insights" element={<Insights />} />
          <Route path="activity" element={<Activity />} />
          <Route path="profile" element={<Profile />} />
        </Route>
        <Route element={<PublicLayout />}>
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </>
  )
}
