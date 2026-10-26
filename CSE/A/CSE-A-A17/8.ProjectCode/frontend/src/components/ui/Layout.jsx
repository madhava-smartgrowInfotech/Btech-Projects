import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import {
  BarChart3,
  Check,
  Cpu,
  Gauge,
  Info,
  LayoutDashboard,
  Menu,
  Moon,
  Shirt,
  Shuffle,
  SlidersHorizontal,
  Sparkles,
  Sun,
  Table2,
  TrendingUp,
  UploadCloud,
} from 'lucide-react'
import { useTheme } from '../../lib/theme'
import { usePipeline } from '../../lib/pipeline'
import { Button, IconButton } from './Button'
import { Drawer } from './Feedback'

/** The pipeline, in the order the README walks through it. `done` reads a flag from /api/state. */
export const APP_NAV = [
  { to: '/app', label: 'Overview', short: 'Home', icon: LayoutDashboard, end: true },
  { to: '/app/upload', label: 'Data upload', short: 'Upload', icon: UploadCloud, done: 'data_loaded', step: '01' },
  { to: '/app/explore', label: 'Data exploration', short: 'Explore', icon: BarChart3, done: 'daily_ready', step: '02' },
  { to: '/app/demand', label: 'Demand analysis', short: 'Demand', icon: Table2, done: 'daily_ready', step: '03' },
  { to: '/app/features', label: 'Feature engineering', short: 'Features', icon: SlidersHorizontal, done: 'features_ready', step: '04' },
  { to: '/app/training', label: 'Model training', short: 'Train', icon: Cpu, done: 'xgboost_trained', step: '05' },
  { to: '/app/domain', label: 'Domain adaptation', short: 'Domain', icon: Shuffle, done: 'domain_done', step: '06' },
  { to: '/app/evaluation', label: 'Model evaluation', short: 'Evaluate', icon: Gauge, done: 'xgboost_trained', step: '07' },
  { to: '/app/forecast', label: 'Demand forecast', short: 'Forecast', icon: TrendingUp, done: 'forecast_done', step: '08' },
  { to: '/app/insights', label: 'AI insights', short: 'AI', icon: Sparkles, step: '09' },
]
const BOTTOM = ['/app', '/app/upload', '/app/training', '/app/domain', '/app/forecast']
const PUBLIC_NAV = [
  { to: '/about', label: 'About project', icon: Info },
]

export function Container({ children, className = '', style }) {
  return (
    <div className={`container ${className}`} style={style}>
      {children}
    </div>
  )
}

export function Brand() {
  return (
    <Link to="/" className="brand" aria-label="TrendCast home">
      <span className="brand-mark" aria-hidden="true">
        ✦
      </span>
      <span>
        TREND
        <br />
        CAST
      </span>
    </Link>
  )
}

export function ThemeToggle() {
  const { theme, toggle } = useTheme()
  return <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
}

function NavList({ items, onNavigate, state }) {
  return (
    <nav className="sidebar-nav" aria-label="Main">
      {items.map(({ to, label, icon: Icon, end, done, step }) => {
        const complete = done && state?.[done]
        return (
          <NavLink key={to} to={to} end={end} className="nav-link" onClick={onNavigate}>
            <Icon size={20} aria-hidden="true" />
            <span className="nav-label">{label}</span>
            {step && !complete && (
              <span className="nav-step" aria-hidden="true">
                {step}
              </span>
            )}
            {complete && (
              <span className="nav-done" title="Done">
                <Check size={12} strokeWidth={4} aria-hidden="true" />
                <span className="sr-only">done</span>
              </span>
            )}
          </NavLink>
        )
      })}
    </nav>
  )
}

function Progress({ state }) {
  const flags = ['data_loaded', 'daily_ready', 'features_ready', 'xgboost_trained', 'domain_done', 'forecast_done']
  const n = state ? flags.filter((f) => state[f]).length : 0
  return (
    <div className="card card-flat" style={{ padding: 12 }}>
      <div className="row-between">
        <strong className="tiny mono">PIPELINE</strong>
        <span className="tiny mono">
          {n}/{flags.length}
        </span>
      </div>
      <div className="progress" role="progressbar" aria-label="Pipeline progress" aria-valuemin={0} aria-valuemax={flags.length} aria-valuenow={n} style={{ marginTop: 8 }}>
        <div className="progress-bar" style={{ width: `${(n / flags.length) * 100}%` }} />
      </div>
    </div>
  )
}

export function Sidebar({ onNavigate }) {
  const { state } = usePipeline()
  return (
    <aside className="sidebar">
      <Brand />
      <div className="divider-label">Pipeline</div>
      <NavList items={APP_NAV} onNavigate={onNavigate} state={state} />
      <div className="divider-label">Project</div>
      <NavList items={PUBLIC_NAV} onNavigate={onNavigate} />
      <div className="sidebar-foot">
        <Progress state={state} />
      </div>
    </aside>
  )
}

export function Topbar({ title, onMenu }) {
  return (
    <header className="topbar">
      {onMenu && <IconButton icon={Menu} label="Open navigation" className="only-mobile" onClick={onMenu} />}
      <span className="only-mobile">
        <Brand />
      </span>
      {title && <span className="topbar-title only-desktop">{title}</span>}
      <span className="topbar-spacer" />
      <ThemeToggle />
    </header>
  )
}

/** App layout: sidebar + topbar + content; sidebar becomes a drawer + bottom bar on small screens. */
export function AppShell({ children }) {
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  const { state } = usePipeline()
  useEffect(() => setOpen(false), [loc.pathname])
  const current = APP_NAV.find((n) => (n.end ? loc.pathname === n.to : loc.pathname.startsWith(n.to)))
  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={current ? `TrendCast / ${current.label}` : 'TrendCast'} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          {children}
        </main>
      </div>
      <nav className="bottombar" aria-label="Quick navigation">
        {APP_NAV.filter((n) => BOTTOM.includes(n.to)).map(({ to, short, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end}>
            <Icon size={20} aria-hidden="true" />
            {short}
          </NavLink>
        ))}
      </nav>
      <Drawer open={open} onClose={() => setOpen(false)} title="Menu" side="left">
        <div className="stack">
          <NavList items={[...APP_NAV, ...PUBLIC_NAV]} onNavigate={() => setOpen(false)} state={state} />
          <Progress state={state} />
        </div>
      </Drawer>
    </div>
  )
}

/** Public layout (landing, about): topbar with nav + content. */
export function PublicShell({ children }) {
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  useEffect(() => setOpen(false), [loc.pathname])
  return (
    <>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <header className="topbar">
        <IconButton icon={Menu} label="Open navigation" className="only-mobile" onClick={() => setOpen(true)} />
        <Brand />
        <span className="topbar-spacer" />
        <nav className="public-nav" aria-label="Main">
          {PUBLIC_NAV.map((n) => (
            <NavLink key={n.to} to={n.to}>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <ThemeToggle />
        <Button variant="primary" size="sm" to="/app" icon={LayoutDashboard} className="only-desktop">
          Open the app
        </Button>
      </header>
      <main id="main" tabIndex={-1}>
        {children}
      </main>
      <Drawer open={open} onClose={() => setOpen(false)} title="Menu" side="left">
        <div className="stack">
          <NavList items={[{ to: '/', label: 'Home', icon: Shirt, end: true }, ...PUBLIC_NAV]} onNavigate={() => setOpen(false)} />
          <Button variant="primary" to="/app" icon={LayoutDashboard} block>
            Open the app
          </Button>
        </div>
      </Drawer>
    </>
  )
}

export function PageHeader({ eyebrow, title, description, actions, crumbs }) {
  return (
    <header className="page-header">
      <div style={{ minWidth: 0 }}>
        {crumbs}
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h1 style={{ marginTop: eyebrow ? 10 : 0, overflowWrap: 'anywhere' }}>{title}</h1>
        {description && <p className="desc">{description}</p>}
      </div>
      {actions && <div className="row">{actions}</div>}
    </header>
  )
}
