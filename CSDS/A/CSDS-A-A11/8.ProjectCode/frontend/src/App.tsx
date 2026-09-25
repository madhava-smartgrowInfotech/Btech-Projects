import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Toaster } from '@/components/ui/toast'
import { RootLayout } from '@/components/layout/RootLayout'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { Skeleton } from '@/components/ui/skeleton'
import Home from '@/pages/Home'
import Shop from '@/pages/Shop'
import ProductDetail from '@/pages/ProductDetail'
import Cart from '@/pages/Cart'
import NotFound from '@/pages/NotFound'

// The console pulls in the whole charting layer — keep it out of the storefront bundle.
const Intelligence = lazy(() => import('@/pages/Intelligence'))

function RouteFallback() {
  return (
    <div className="container space-y-6 py-16">
      <Skeleton className="h-4 w-40" />
      <Skeleton className="h-12 w-2/3 max-w-xl" />
      <div className="grid gap-4 sm:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-40 rounded-2xl" />
        ))}
      </div>
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <TooltipProvider delayDuration={180} skipDelayDuration={400}>
        <Routes>
          <Route element={<RootLayout />}>
            <Route index element={<Home />} />
            <Route path="shop" element={<Shop />} />
            <Route path="shop/:category" element={<Shop />} />
            <Route path="product/:slug" element={<ProductDetail />} />
            <Route path="cart" element={<Cart />} />
            <Route
              path="intelligence"
              element={
                <Suspense fallback={<RouteFallback />}>
                  <Intelligence />
                </Suspense>
              }
            />
            <Route path="products/:slug" element={<Navigate to="/shop" replace />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
        <Toaster />
      </TooltipProvider>
    </ErrorBoundary>
  )
}
