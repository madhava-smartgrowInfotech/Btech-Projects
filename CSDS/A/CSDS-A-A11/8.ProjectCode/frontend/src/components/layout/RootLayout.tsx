import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Header } from './Header'
import { Footer } from './Footer'
import { scrollToTop, useSmoothScroll } from '@/hooks/useSmoothScroll'
import { refreshScrollTriggers } from '@/hooks/useReveal'
import { EASE_EXPO } from '@/lib/utils'

export function RootLayout() {
  const location = useLocation()
  useSmoothScroll()

  useEffect(() => {
    scrollToTop(true)
    refreshScrollTriggers()
  }, [location.pathname, location.search])

  const isConsole = location.pathname.startsWith('/intelligence')

  return (
    <div className="relative flex min-h-screen flex-col">
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 -z-10 bg-ink-950 bg-grid-fade bg-grid opacity-[0.55]"
        style={{
          maskImage: 'radial-gradient(90% 60% at 50% 0%, black, transparent 78%)',
          WebkitMaskImage: 'radial-gradient(90% 60% at 50% 0%, black, transparent 78%)',
        }}
      />
      <Header />
      <main className="flex-1 pt-[68px]">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.42, ease: EASE_EXPO }}
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>
      {!isConsole && <Footer />}
    </div>
  )
}
