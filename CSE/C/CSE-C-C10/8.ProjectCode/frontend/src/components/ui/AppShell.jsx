import { BarChart3, Keyboard, LayoutDashboard, LogOut, Menu, Moon, Rocket, Search, Sun, TerminalSquare, TrendingUp } from 'lucide-react'
import { Suspense, useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import api from '../../api'
import { logEvent } from '../../lib/activity'
import { useAuth } from '../../lib/auth'
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
  { to: '/app', label: 'Dashboard', icon: LayoutDashboard, end: true, key: 'd' },
  { to: '/app/analyze', label: 'Analyze a startup', icon: Rocket, key: 'a' },
  { to: '/app/performance', label: 'Model performance', icon: BarChart3, key: 'p' },
  { to: '/app/insights', label: 'Startup insights', icon: TrendingUp, key: 'i' },
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

export function Sidebar({ model, health, onPick }) {
  const { user, signOut } = useAuth()
  return (
    <div className="flex h-full flex-col gap-6 p-4">
      <Link to="/" className="px-1"><Logo /></Link>
      <div>
        <div className="mb-2 px-3 font-mono text-[10px] uppercase tracking-[0.16em] text-dim">Workspace</div>
        <NavList onPick={onPick} />
      </div>
      <div className="mt-auto space-y-3">
        <div className="rounded-[6px] border border-line bg-panel-2 p-3 font-mono text-[11px] leading-relaxed text-muted">
          <div className="mb-1 flex items-center justify-between text-[10px] uppercase tracking-[0.14em] text-dim">
            <span>Serving model</span>
            <StatusDot tone={health === 'ok' ? 'ok' : health === 'down' ? 'alert' : 'warn'} />
          </div>
          {model ? (
            <>
              <div className="text-fg">{model.best_model}</div>
              <div>{model.records.toLocaleString('en-US')} historical startups</div>
            </>
          ) : <div>{health === 'down' ? 'API unreachable' : 'loading…'}</div>}
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

function Topbar({ onMenu, onSearch, onLog, onHelp, health, gPending }) {
  const { theme, toggle } = useTheme()
  const { pathname } = useLocation()
  const healthText = { ok: 'API online · model loaded', down: 'API unreachable' }[health] || 'checking API'
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-bg/80 backdrop-blur-md">
      <div className="flex h-14 items-center gap-2 px-4 sm:px-6 lg:px-8">
        <IconButton icon={Menu} label="Open navigation" className="lg:hidden" onClick={onMenu} />
        <Link to="/app" className="lg:hidden"><Logo compact /></Link>
        <div className="hidden min-w-0 truncate font-mono text-xs text-dim sm:block">
          <span className="text-ok">~</span>{pathname.replace(/^\/app/, '') || '/dashboard'}
        </div>
        <div className="flex-1" />
        <button type="button" onClick={onSearch}
          className="flex h-9 items-center gap-2 rounded-[6px] border border-line-strong bg-panel-2 px-2.5 text-sm text-dim transition-colors hover:border-ok/50 hover:text-fg sm:w-64">
          <Search size={15} aria-hidden="true" />
          <span className="hidden flex-1 text-left sm:inline">Jump to a screen…</span>
          <kbd className="hidden rounded border border-line-strong px-1.5 font-mono text-[10px] sm:inline">/</kbd>
          <span className="sr-only sm:hidden">Search</span>
        </button>
        {gPending && <kbd className="rounded border border-ok/60 px-1.5 py-0.5 font-mono text-[11px] text-ok" aria-live="polite">g…</kbd>}
        <Tooltip content={healthText} align="end">
          <span className="hidden px-1.5 sm:inline-flex" role="status" aria-label={healthText}>
            <StatusDot tone={health === 'ok' ? 'ok' : health === 'down' ? 'alert' : 'warn'} ring={health === 'ok'} />
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
  ['/', 'Jump to a screen'], ['g d', 'Dashboard'], ['g a', 'Analyze a startup'], ['g p', 'Model performance'],
  ['g i', 'Startup insights'], ['g l', 'Activity log'], ['?', 'This help'], ['Esc', 'Close any overlay'],
]

export default function AppShell() {
  const navigate = useNavigate()
  const [palette, setPalette] = useState(false)
  const [log, setLog] = useState(false)
  const [help, setHelp] = useState(false)
  const [menu, setMenu] = useState(false)
  const [gPending, setGPending] = useState(false)
  const [health, setHealth] = useState(null)
  const [model, setModel] = useState(null)
  const overlay = palette || log || help || menu
  const overlayRef = useRef(overlay)
  overlayRef.current = overlay

  // keyboard-first navigation
  useEffect(() => {
    let pending = false
    let timer
    const GO = { d: '/app', a: '/app/analyze', p: '/app/performance', i: '/app/insights' }
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

  // API health (silent polling; transitions are logged)
  useEffect(() => {
    let prev = null
    const check = () => api.get('/health', { silent: true })
      .then((r) => {
        if (prev !== 'ok') logEvent('health', `api online · ${r.data.best_model} · ${r.data.records} historical startups`)
        prev = 'ok'
        setModel(r.data)
        setHealth('ok')
      })
      .catch(() => {
        if (prev !== 'down') logEvent('error', 'api unreachable on /api/health')
        prev = 'down'
        setHealth('down')
      })
    check()
    const id = setInterval(check, 20000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="relative min-h-screen">
      <Backdrop intensity={0.55} className="fixed inset-x-0 top-0 z-0 h-[70vh] fade-mask-bottom opacity-70" />
      <a href="#main" className="sr-only z-50 rounded bg-ok px-3 py-2 text-on-ok focus:not-sr-only focus:fixed focus:left-3 focus:top-3">Skip to content</a>
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-line bg-panel/85 backdrop-blur-md lg:block">
        <Sidebar model={model} health={health} />
      </aside>
      <div className="relative lg:pl-64">
        <Topbar onMenu={() => setMenu(true)} onSearch={() => setPalette(true)} onLog={() => setLog(true)} onHelp={() => setHelp(true)} health={health} gPending={gPending} />
        <main id="main" className="py-6 sm:py-8">
          <Container>
            <Suspense fallback={<PageSkeleton />}>
              <PageTransition><Outlet /></PageTransition>
            </Suspense>
          </Container>
        </main>
      </div>

      <Drawer open={menu} onClose={() => setMenu(false)} side="left" title="Navigation" width="w-[min(300px,86vw)]">
        <Sidebar model={model} health={health} onPick={() => setMenu(false)} />
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
