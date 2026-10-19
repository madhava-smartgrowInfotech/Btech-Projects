import { Suspense, lazy, useEffect } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation, useSearchParams } from 'react-router-dom'
import { AppShell, Skeleton, useToast } from './components/ui'
import { useAuth } from './lib/auth'

const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Find = lazy(() => import('./pages/Find'))
const Bookings = lazy(() => import('./pages/Bookings'))
const Trust = lazy(() => import('./pages/Trust'))
const AdminOverview = lazy(() => import('./pages/admin/Overview'))
const AdminLocations = lazy(() => import('./pages/admin/Locations'))
const AdminInsights = lazy(() => import('./pages/admin/Insights'))
const AdminBookings = lazy(() => import('./pages/admin/Bookings'))
const AdminUsers = lazy(() => import('./pages/admin/Users'))
const NotFound = lazy(() => import('./pages/NotFound'))

const PageFallback = () => (
  <div className="container" aria-busy="true" aria-label="Loading page">
    <Skeleton height={34} width={260} style={{ marginBottom: 18 }} />
    <Skeleton height={140} style={{ marginBottom: 14 }} />
    <Skeleton height={220} />
  </div>
)

function RequireAuth() {
  const { user, booting, leftOnPurpose } = useAuth()
  const loc = useLocation()
  if (booting) return <PageFallback />
  if (!user && leftOnPurpose) return <Navigate to="/" replace />
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname + loc.search }} />
  return <AppShell />
}

function RequireAdmin() {
  const { user } = useAuth()
  const toast = useToast()
  useEffect(() => {
    if (user && user.role !== 'admin') toast({ tone: 'error', title: 'Admins only', message: 'Your account is a driver account, so the admin screens are hidden.' })
  }, [user, toast])
  if (user?.role !== 'admin') return <Navigate to="/app/find" replace />
  return <Outlet />
}

// Stripe sends people back to /?paid=<id> or /?cancelled=<id>; tell them what happened.
function PaymentReturn() {
  const [params, setParams] = useSearchParams()
  const toast = useToast()
  useEffect(() => {
    const paid = params.get('paid')
    const cancelled = params.get('cancelled')
    if (!paid && !cancelled) return
    if (paid) toast({ tone: 'success', title: 'Payment received', message: `Thanks - booking #${paid} will show as paid in My bookings once Stripe confirms it.`, duration: 9000 })
    else toast({ tone: 'info', title: 'Payment cancelled', message: `Booking #${cancelled} is still reserved. You can pay from My bookings.`, duration: 9000 })
    setParams({}, { replace: true })
  }, [params, setParams, toast])
  return null
}

export default function App() {
  return (
    <>
      <PaymentReturn />
      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/app" element={<RequireAuth />}>
            <Route index element={<Navigate to="find" replace />} />
            <Route path="find" element={<Find />} />
            <Route path="bookings" element={<Bookings />} />
            <Route path="trust" element={<Trust />} />
            <Route path="admin" element={<RequireAdmin />}>
              <Route index element={<AdminOverview />} />
              <Route path="locations" element={<AdminLocations />} />
              <Route path="insights" element={<AdminInsights />} />
              <Route path="bookings" element={<AdminBookings />} />
              <Route path="users" element={<AdminUsers />} />
            </Route>
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </>
  )
}
