import { BarChart3, Brain, Cpu, Keyboard, LayoutDashboard, ListTree, LogOut, Menu, Moon, Search, Settings, ShieldAlert, Sun, TerminalSquare } from 'lucide-react'
import { Suspense, useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../lib/auth'
import { useLive } from '../../lib/live'
import { useTheme } from '../../lib/theme'
import { PageTransition } from '../motion'
import Backdrop from '../reactbits/Backdrop'
import ActivityLog from './ActivityLog'
import CommandPalette from './CommandPalette'
import { IconButton } from './controls'
import { StatusDot } from './display'
import { Drawer, Modal, PageSkeleton, Tooltip } from './feedback'
import { Breadcrumbs } from './nav'
import Logo from './Logo'
import Typewriter from './Typewriter'

export { Logo }

export const NAV = [
  { to: '/app', label: 'Overview', icon: LayoutDashboard, end: true, key: 'o' },
  { to: '/app/detections', label: 'Detections', icon: ListTree, key: 'd' },
  { to: '/app/analytics', label: 'Analytics', icon: BarChart3, key: 'a' },
  { to: '/app/health', label: 'Network health', icon: Cpu, key: 'n' },
  { to: '/app/mitigation', label: 'Mitigation', icon: ShieldAlert, key: 'm' },
  { to: '/app/model', label: 'Model', icon: Brain, key: 'p' },
  { to: '/app/settings', label: 'Settings', icon: Settings, key: 's' },
]

export function Container({ children, className = '' }) {
  return <div className={`mx-auto w-full max-w-[1440px] px-4 sm:px-6 lg:px-8 ${className}`}>{children}</div>
}

export function PageHeader({ title, eyebrow, subtitle, crumbs, actions }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        {crumbs && <div className="mb-2"><Breadcrumbs items={crumbs} /></div>}
        {eyebrow && <div className="mb-1 font-mono text-[11px] uppercase tracking-[0.16em] text-ok">{eyebrow}</div>}
        <Typewriter as="h1" text={title} className="font-mono text-xl font-semibold tracking-tight text-fg sm:text-2xl" />
        {subtitle && <p className="mt-1.5 max-w-3xl text-sm text-muted">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  )
}

function NavList({ onPick }) {
  return (
    <nav aria-label="Main" className="flex flex-col gap-0.5">
      {NAV.map(({ to, label, icon: Icon, end, key }) => (
        <NavLink key={to} to={to} end={end} onClick={onPick}
          className={({ isActive }) => `group relative flex items-center gap-3 rounded-[6px] px-3 py-2 text-sm transition-colors ${isActive ? 'bg-ok/10 text-fg' : 'text-muted hover:bg-panel-2 hover:text-fg'}`}>
          {({ isActive }) => (
            <>
              {isActive && <span className="absolute inset-y-1.5 left-0 w-[2px] rounded bg-ok" aria-hidden="true" />}
              <Icon size={16} className={isActive ? 'text-ok' : 'text-dim group-hover:text-muted'} aria-hidden="true" />
              <span className="flex-1">{label}</span>
              <kbd className="hidden font-mono text-[10px] text-dim lg:inline">g {key}</kbd>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}

const MODE = {
  live: ['alert', 'Live capture'],
  simulation: ['warn', 'Simulation mode'],
  stopped: ['dim', 'Stopped'],
}

export function Sidebar({ onPick }) {
  const { user, signOut } = useAuth()
  const { status, error, loaded } = useLive()
  const [tone, label] = error ? ['alert', 'API unreachable'] : !loaded ? ['warn', 'connecting…'] : MODE[status?.mode] || MODE.stopped
  return (
    <div className="flex h-full flex-col gap-6 p-4">
      <Link to="/" className="px-1"><Logo /></Link>
      <div>
        <div className="mb-2 px-3 font-mono text-[10px] uppercase tracking-[0.16em] text-dim">Console</div>
        <NavList onPick={onPick} />
      </div>
      <div className="mt-auto space-y-3">
        <div className="rounded-[6px] border border-line bg-panel-2 p-3 font-mono text-[11px] leading-relaxed text-muted">
          <div className="mb-1 flex items-center justify-between text-[10px] uppercase tracking-[0.14em] text-dim">
            <span>Session</span>
            <StatusDot tone={tone} blink={status?.monitoring} />
          </div>
          <div className="text-fg">{label}</div>
          {status && !error && (
            <div>{status.monitoring ? `${status.window_seconds}s windows · ${status.windows_completed} done` : 'start a session to monitor'}</div>
          )}
          {error && <div>run.bat starts the backend</div>}
        </div>
        <div className="flex items-center gap-2 border-t border-line px-1 pt-3">
          <div className="grid h-8 w-8 shrink-0 place-items-center rounded-[6px] border border-line-strong font-mono text-xs text-ok">
            {(user?.name || '?').slice(0, 1).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm text-fg">{user?.name}</div>
            <div className="truncate font-mono text-[11px] text-dim">{user?.email}</div>
          </div>
          <IconButton icon={LogOut} label="Sign out" size="sm" onClick={signOut} />
        </div>
      </div>
    </div>
  )
}

function Topbar({ onMenu, onSearch, onLog, onHelp, gPending }) {
  const { theme, toggle } = useTheme()
  const { pathname } = useLocation()
  const { status, error, loaded } = useLive()
  const health = error ? 'down' : !loaded ? 'loading' : 'ok'
  const [mTone, mLabel] = MODE[status?.mode] || MODE.stopped
  const healthText = { ok: `API online · ${mLabel.toLowerCase()}`, loading: 'Connecting to API', down: 'API unreachable' }[health]
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-bg/80 backdrop-blur-md">
      <div className="flex h-14 items-center gap-2 px-4 sm:px-6 lg:px-8">
        <IconButton icon={Menu} label="Open navigation" className="lg:hidden" onClick={onMenu} />
        <Link to="/app" className="lg:hidden"><Logo compact /></Link>
        <div className="hidden min-w-0 truncate font-mono text-xs text-dim sm:block">
          <span className="text-ok">~</span>{pathname.replace(/^\/app/, '') || '/overview'}
        </div>
        <div className="flex-1" />
        <button type="button" onClick={onSearch}
          className="flex h-9 items-center gap-2 rounded-[6px] border border-line-strong bg-panel-2 px-2.5 text-sm text-dim transition-colors hover:border-ok/50 hover:text-fg sm:w-64">
          <Search size={15} aria-hidden="true" />
          <span className="hidden flex-1 text-left sm:inline">Search detections…</span>
          <kbd className="hidden rounded border border-line-strong px-1.5 font-mono text-[10px] sm:inline">/</kbd>
          <span className="sr-only sm:hidden">Search</span>
        </button>
        {status && !error && (
          <span className="hidden items-center md:inline-flex">
            <StatusDot tone={mTone} blink={status.monitoring} label={mLabel} />
          </span>
        )}
        {gPending && <kbd className="rounded border border-ok/60 px-1.5 py-0.5 font-mono text-[11px] text-ok" aria-live="polite">g…</kbd>}
        <Tooltip content={healthText} align="end">
          <span className="hidden px-1.5 sm:inline-flex" role="status" aria-label={healthText}>
            <StatusDot tone={health === 'ok' ? 'ok' : health === 'loading' ? 'warn' : 'alert'} ring={health === 'ok'} />
          </span>
        </Tooltip>
        <IconButton icon={TerminalSquare} label="Activity log (g l)" onClick={onLog} tooltipAlign="end" />
        <span className="hidden sm:inline-flex"><IconButton icon={Keyboard} label="Keyboard shortcuts (?)" onClick={onHelp} tooltipAlign="end" /></span>
        <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} tooltipAlign="end" />
      </div>
    </header>
  )
}

const SHORTCUTS = [
  ['/', 'Search detections / jump to a screen'], ['g o', 'Overview'], ['g d', 'Detections'], ['g a', 'Analytics'], ['g n', 'Network health'],
  ['g m', 'Mitigation'], ['g p', 'Model'], ['g s', 'Settings'], ['g l', 'Activity log'], ['?', 'This help'], ['Esc', 'Close any overlay'],
]

export default function AppShell() {
  const navigate = useNavigate()
  const [palette, setPalette] = useState(false)
  const [log, setLog] = useState(false)
  const [help, setHelp] = useState(false)
  const [menu, setMenu] = useState(false)
  const [gPending, setGPending] = useState(false)
  const overlay = palette || log || help || menu
  const overlayRef = useRef(overlay)
  overlayRef.current = overlay

  // keyboard-first navigation
  useEffect(() => {
    let pending = false
    let timer
    const GO = { o: '/app', d: '/app/detections', a: '/app/analytics', n: '/app/health', m: '/app/mitigation', p: '/app/model', s: '/app/settings' }
    function onKey(e) {
      if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey || overlayRef.current) return
      if (e.target.closest?.('input, textarea, select, [contenteditable="true"]')) return
      if (pending) {
        pending = false
        setGPending(false)
        clearTimeout(timer)
        const k = e.key.toLowerCase()
        if (k === 'l') { e.preventDefault(); setLog(true) }
        else if (GO[k]) { e.preventDefault(); navigate(GO[k]) }
        return
      }
      if (e.key === '/') { e.preventDefault(); setPalette(true) }
      else if (e.key === '?') { e.preventDefault(); setHelp(true) }
      else if (e.key === 'g') {
        pending = true
        setGPending(true)
        timer = setTimeout(() => { pending = false; setGPending(false) }, 1500)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => { window.removeEventListener('keydown', onKey); clearTimeout(timer) }
  }, [navigate])

  return (
    <div className="relative min-h-screen">
      <Backdrop intensity={0.4} className="fixed inset-x-0 top-0 z-0 h-[42vh] fade-mask-bottom opacity-40" />
      <a href="#main" className="sr-only z-50 rounded bg-ok px-3 py-2 text-on-ok focus:not-sr-only focus:fixed focus:left-3 focus:top-3">Skip to content</a>
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-line bg-panel/85 backdrop-blur-md lg:block">
        <Sidebar />
      </aside>
      <div className="relative lg:pl-64">
        <Topbar onMenu={() => setMenu(true)} onSearch={() => setPalette(true)} onLog={() => setLog(true)} onHelp={() => setHelp(true)} gPending={gPending} />
        <main id="main" className="py-6 sm:py-8">
          <Container>
            <Suspense fallback={<PageSkeleton />}>
              <PageTransition><Outlet /></PageTransition>
            </Suspense>
          </Container>
        </main>
      </div>

      <Drawer open={menu} onClose={() => setMenu(false)} side="left" title="Navigation" width="w-[min(300px,86vw)]">
        <Sidebar onPick={() => setMenu(false)} />
      </Drawer>
      <Drawer open={log} onClose={() => setLog(false)} title="Activity log" width="w-[min(560px,96vw)]">
        <div className="p-3"><ActivityLog height="calc(100vh - 140px)" /></div>
      </Drawer>
      <CommandPalette open={palette} onClose={() => setPalette(false)} nav={NAV} />
      <Modal open={help} onClose={() => setHelp(false)} title="Keyboard shortcuts" size="sm">
        <ul className="p-4">
          {SHORTCUTS.map(([k, v]) => (
            <li key={k} className="flex items-center justify-between border-b border-dashed border-line py-2 text-sm last:border-0">
              <span className="text-muted">{v}</span>
              <kbd className="rounded border border-line-strong bg-panel-2 px-2 py-0.5 font-mono text-[11px] text-ok">{k}</kbd>
            </li>
          ))}
        </ul>
      </Modal>
    </div>
  )
}
