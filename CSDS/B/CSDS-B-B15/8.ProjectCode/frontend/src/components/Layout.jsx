import { Link, Outlet, useNavigate } from 'react-router-dom'
import { Moon, Sun } from 'lucide-react'
import { homeFor, useAuth } from '../auth'
import { useTheme } from '../lib/theme'
import { Button, IconButton } from './ui/controls'
import { Skeleton } from './ui/feedback'
import Logo from './ui/Logo'
import { Suspense } from 'react'

// Layout for the public pages (landing, login): slim header, theme switch, footer with map attribution.
export default function Layout() {
  const { user } = useAuth()
  const nav = useNavigate()
  const { theme, toggle } = useTheme()
  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded focus:bg-ok focus:px-3 focus:py-2 focus:text-on-ok">
        Skip to content
      </a>
      <header className="sticky top-0 z-30 border-b border-line bg-bg/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-[1440px] items-center gap-2 px-4 sm:px-6 lg:px-8">
          <Link to="/" aria-label="MediQueue home">
            <Logo />
          </Link>
          <div className="flex-1" />
          <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} tooltipAlign="end" />
          {user ? (
            <Button size="sm" variant="secondary" onClick={() => nav(homeFor(user))}>
              Open app
            </Button>
          ) : (
            <Button size="sm" variant="secondary" onClick={() => nav('/login')}>
              Log in
            </Button>
          )}
        </div>
      </header>
      <main id="main" className="mx-auto w-full max-w-[1440px] flex-1 px-4 py-8 sm:px-6 lg:px-8">
        <Suspense fallback={<Skeleton className="h-64 w-full" />}>
          <Outlet />
        </Suspense>
      </main>
      <footer className="border-t border-line px-4 py-4 text-center font-mono text-[11px] leading-relaxed text-dim">
        MediQueue is decision support, not a diagnosis. In an emergency call 108. Map data &copy;{' '}
        <a className="underline hover:text-fg" href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">
          OpenStreetMap
        </a>{' '}
        contributors.
      </footer>
    </div>
  )
}
