import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  ArrowLeftRight,
  BarChart3,
  Boxes,
  Home,
  LayoutDashboard,
  MapPinned,
  Menu,
  Moon,
  RefreshCcw,
  Sun,
  TrendingUp,
} from 'lucide-react'
import { api } from '../../lib/api'
import { spring } from '../../lib/motion'
import { useTheme } from '../../lib/theme'
import { PageTransition } from '../motion'
import { Breadcrumbs } from './Nav'
import { IconButton } from './Button'
import { Drawer, Tooltip } from './Overlay'

export const NAV = [
  { to: '/app', label: 'Dashboard', short: 'Home', icon: LayoutDashboard, tone: 'var(--lavender)', end: true },
  { to: '/app/forecast', label: 'Forecast', short: 'Forecast', icon: TrendingUp, tone: 'var(--mint)' },
  { to: '/app/plan', label: 'Plan hubs', short: 'Plan', icon: Boxes, tone: 'var(--peach)' },
  { to: '/app/compare', label: 'Compare methods', short: 'Compare', icon: BarChart3, tone: 'var(--sky)' },
  { to: '/app/rolling', label: 'Re-optimise', short: 'Rolling', icon: RefreshCcw, tone: 'var(--rose)' },
  { to: '/app/regions', label: 'Regions', short: 'Regions', icon: MapPinned, tone: 'var(--butter)' },
]

export function Container({ children, className = '', style }) {
  return (
    <div className={`container ${className}`} style={style}>
      {children}
    </div>
  )
}

export function Brand({ to = '/' }) {
  return (
    <Link to={to} className="brand" aria-label="HubOptima home">
      <motion.span className="brand-mark" whileHover={{ rotate: -8, scale: 1.06 }} whileTap={{ scale: 0.92 }} transition={spring}>
        <ArrowLeftRight size={20} aria-hidden="true" />
      </motion.span>
      <span className="brand-name">
        HubOptima
        <span className="brand-sub">Forecast-driven hub location</span>
      </span>
    </Link>
  )
}

function NavItems({ onNavigate, layoutId = 'nav-pill' }) {
  return (
    <nav className="nav" aria-label="Main">
      <span className="nav-label">Workspace</span>
      {NAV.map((n) => (
        <NavLink key={n.to} to={n.to} end={n.end} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={onNavigate}>
          {({ isActive }) => (
            <>
              {isActive && <motion.span layoutId={layoutId} className="nav-pill" transition={spring} />}
              <motion.span className="nav-ico" style={{ background: n.tone, color: 'var(--on-pastel)' }} whileHover={{ scale: 1.1, rotate: -6 }} transition={spring}>
                <n.icon size={17} aria-hidden="true" />
              </motion.span>
              <span>{n.label}</span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}

export function Sidebar({ health }) {
  return (
    <aside className="sidebar">
      <Brand />
      <NavItems />
      <div className="sidebar-foot">
        <strong style={{ display: 'block', color: 'var(--text)', marginBottom: 4 }}>Solver</strong>
        {health ? (health.has_pulp ? 'CBC via PuLP - exact sub-problems available.' : 'Greedy fallback - install pulp for exact MIPs.') : 'Checking…'}
      </div>
    </aside>
  )
}

function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const dark = theme === 'dark'
  return (
    <Tooltip content={dark ? 'Switch to light mode' : 'Switch to dark mode'}>
      <motion.button
        type="button"
        className="icon-btn"
        onClick={toggle}
        aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
        aria-pressed={dark}
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.88 }}
        transition={spring}
      >
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={theme}
            initial={{ rotate: -90, scale: 0.4, opacity: 0 }}
            animate={{ rotate: 0, scale: 1, opacity: 1 }}
            exit={{ rotate: 90, scale: 0.4, opacity: 0 }}
            transition={spring}
            style={{ display: 'grid' }}
          >
            {dark ? <Sun size={20} aria-hidden="true" /> : <Moon size={20} aria-hidden="true" />}
          </motion.span>
        </AnimatePresence>
      </motion.button>
    </Tooltip>
  )
}

export function Topbar({ title, health, healthError, onMenu }) {
  const navigate = useNavigate()
  const state = healthError ? 'bad' : health ? '' : 'wait'
  return (
    <header className="topbar">
      <IconButton icon={Menu} label="Open navigation" className="menu-btn" onClick={onMenu} />
      <Brand />
      <span className="topbar-title">{title}</span>
      <span className="topbar-spacer" />
      <span className="status-pill" role="status" title={healthError ? 'API offline' : health?.solver}>
        <span className={`status-dot ${state}`} aria-hidden="true" />
        <span className="status-text">{healthError ? 'API offline' : health ? `API online · ${health.has_pulp ? 'CBC' : 'greedy'}` : 'Connecting…'}</span>
        <span className="sr-only">{healthError ? 'API offline' : health ? 'API online' : 'Connecting'}</span>
      </span>
      <span className="home-btn">
        <Tooltip content="Back to the landing page">
          <IconButton icon={Home} label="Landing page" onClick={() => navigate('/')} />
        </Tooltip>
      </span>
      <ThemeToggle />
    </header>
  )
}

export function PageHeader({ eyebrow, icon: Icon, title, lead, actions, crumbs }) {
  return (
    <div>
      {crumbs && <Breadcrumbs items={crumbs} />}
      <div className="page-header">
        <div style={{ minWidth: 0 }}>
          {eyebrow && (
            <span className="eyebrow">
              {Icon && <Icon size={14} aria-hidden="true" />}
              {eyebrow}
            </span>
          )}
          <h1>{title}</h1>
          {lead && <p className="lead">{lead}</p>}
        </div>
        {actions && <div className="row">{actions}</div>}
      </div>
    </div>
  )
}

function useHealth() {
  const [s, setS] = useState({ data: null, error: null })
  useEffect(() => {
    let alive = true
    const check = () =>
      api
        .health()
        .then((d) => alive && setS({ data: d, error: null }))
        .catch((e) => alive && setS({ data: null, error: e }))
    check()
    const t = setInterval(check, 30000)
    return () => {
      alive = false
      clearInterval(t)
    }
  }, [])
  return s
}

export function AppShell() {
  const loc = useLocation()
  const [open, setOpen] = useState(false)
  const health = useHealth()
  const current = [...NAV].reverse().find((n) => loc.pathname === n.to || loc.pathname.startsWith(`${n.to}/`)) || NAV[0]
  useEffect(() => {
    document.title = `${current.label} · HubOptima`
    window.scrollTo(0, 0)
  }, [current.label])
  return (
    <div className="shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Sidebar health={health.data} />
      <div className="shell-main">
        <Topbar title={current.label} health={health.data} healthError={health.error} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          <Container>
            <AnimatePresence mode="wait">
              <PageTransition key={loc.pathname}>
                <Outlet />
              </PageTransition>
            </AnimatePresence>
          </Container>
        </main>
      </div>
      <nav className="bottombar" aria-label="Quick navigation">
        {NAV.map((n) => (
          <NavLink key={n.to} to={n.to} end={n.end} className={({ isActive }) => (isActive ? 'active' : '')}>
            {({ isActive }) => (
              <>
                {isActive && <motion.span layoutId="bottom-pill" className="nav-pill" transition={spring} />}
                <n.icon size={20} aria-hidden="true" />
                <span>{n.short}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
      <Drawer open={open} onClose={() => setOpen(false)} title="Navigate">
        <NavItems onNavigate={() => setOpen(false)} layoutId="drawer-pill" />
      </Drawer>
    </div>
  )
}
