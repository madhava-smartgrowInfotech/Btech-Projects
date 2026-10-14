import { LogOut, Menu, Moon, Sun, TerminalSquare } from 'lucide-react'
import { Suspense, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { homeFor, useAuth } from '../../auth'
import { navFor } from '../../nav'
import { useTheme } from '../../lib/theme'
import { PageTransition } from '../motion'
import ActivityLog from './ActivityLog'
import { IconButton } from './controls'
import { Drawer, PageSkeleton } from './feedback'
import { Breadcrumbs } from './nav'
import Logo from './Logo'
import Typewriter from './Typewriter'

// MediQueue copy of the kit's AppShell: role-based links, the activity log drawer and the theme switch.
// The kit's TaxSentinel-only parts (pipeline status, command palette, g-key shortcuts) were removed.

export function Container({ children, className = '' }) {
  return <div className={`mx-auto w-full max-w-[1440px] px-4 sm:px-6 lg:px-8 ${className}`}>{children}</div>
}

export function PageHeader({ title, eyebrow, subtitle, crumbs, actions }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        {crumbs && <div className="mb-2"><Breadcrumbs items={crumbs} /></div>}
        {eyebrow && <div className="mb-1 font-mono text-[11px] uppercase tracking-[0.16em] text-ok">{eyebrow}</div>}
        <Typewriter as="h1" text={title} speed={18} className="font-mono text-xl font-semibold tracking-tight text-fg sm:text-2xl" />
        {subtitle && <p className="mt-1.5 max-w-3xl text-sm text-muted">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  )
}

function NavList({ items, onPick }) {
  return (
    <nav aria-label="Main" className="flex flex-col gap-0.5">
      {items.map(({ to, label, icon: Icon }) => (
        <NavLink key={to} to={to} onClick={onPick}
          className={({ isActive }) => `group relative flex items-center gap-3 rounded-[6px] px-3 py-2 text-sm transition-colors ${isActive ? 'bg-ok/10 text-fg' : 'text-muted hover:bg-panel-2 hover:text-fg'}`}>
          {({ isActive }) => (
            <>
              {isActive && <span className="absolute inset-y-1.5 left-0 w-[2px] rounded bg-ok" aria-hidden="true" />}
              <Icon size={16} className={isActive ? 'text-ok' : 'text-dim group-hover:text-muted'} aria-hidden="true" />
              <span className="flex-1">{label}</span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}

function Sidebar({ onPick }) {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const signOut = () => {
    logout()
    nav('/login')
  }
  return (
    <div className="flex h-full flex-col gap-6 p-4">
      <Link to={homeFor(user)} className="px-1" aria-label="MediQueue home"><Logo /></Link>
      <div>
        <div className="mb-2 px-3 font-mono text-[10px] uppercase tracking-[0.16em] text-dim">{user.role} workspace</div>
        <NavList items={navFor(user)} onPick={onPick} />
      </div>
      <div className="mt-auto flex items-center gap-2 border-t border-line px-1 pt-3">
        <div className="grid h-8 w-8 shrink-0 place-items-center rounded-[6px] border border-line-strong font-mono text-xs text-ok" aria-hidden="true">
          {(user.name || '?').slice(0, 1).toUpperCase()}
        </div>
        <div className="min-w-0 flex-1">
          <div className="truncate text-sm text-fg">{user.name}</div>
          <div className="truncate font-mono text-[11px] text-dim">{user.role}</div>
        </div>
        <IconButton icon={LogOut} label="Log out" size="sm" onClick={signOut} />
      </div>
    </div>
  )
}

function Topbar({ onMenu, onLog }) {
  const { theme, toggle } = useTheme()
  const { pathname } = useLocation()
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-bg/80 backdrop-blur-md">
      <div className="flex h-14 items-center gap-2 px-4 sm:px-6 lg:px-8">
        <IconButton icon={Menu} label="Open navigation" className="lg:hidden" onClick={onMenu} />
        <Link to="/" className="lg:hidden" aria-label="MediQueue home"><Logo compact /></Link>
        <div className="hidden min-w-0 truncate font-mono text-xs text-dim sm:block">
          <span className="text-ok">~</span>{pathname}
        </div>
        <div className="flex-1" />
        <IconButton icon={TerminalSquare} label="Activity log" onClick={onLog} tooltipAlign="end" />
        <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} tooltipAlign="end" />
      </div>
    </header>
  )
}

export default function AppShell() {
  const [menu, setMenu] = useState(false)
  const [log, setLog] = useState(false)
  return (
    <div className="min-h-screen">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded focus:bg-ok focus:px-3 focus:py-2 focus:text-on-ok">
        Skip to content
      </a>
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-line bg-panel/85 backdrop-blur-md lg:block">
        <Sidebar />
      </aside>
      <div className="lg:pl-64">
        <Topbar onMenu={() => setMenu(true)} onLog={() => setLog(true)} />
        <main id="main" className="py-6 sm:py-8">
          <Container>
            <Suspense fallback={<PageSkeleton />}>
              <PageTransition>
                <Outlet />
              </PageTransition>
            </Suspense>
          </Container>
        </main>
      </div>

      <Drawer open={menu} onClose={() => setMenu(false)} side="left" title="Navigation" width="w-[min(300px,86vw)]">
        <Sidebar onPick={() => setMenu(false)} />
      </Drawer>
      <Drawer open={log} onClose={() => setLog(false)} title="Activity log" width="w-[min(560px,96vw)]">
        <div className="p-3">
          <ActivityLog height="calc(100vh - 140px)" />
        </div>
      </Drawer>
    </div>
  )
}
