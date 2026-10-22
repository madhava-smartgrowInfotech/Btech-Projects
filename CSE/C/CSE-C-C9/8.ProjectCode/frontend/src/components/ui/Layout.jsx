import { Suspense, useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  BarChart3,
  Brain,
  ClipboardList,
  FlaskConical,
  Home,
  Info,
  LayoutDashboard,
  LineChart,
  LogOut,
  Menu,
  Moon,
  Sun,
  TrendingUp,
} from 'lucide-react'
import { api } from '../../lib/api'
import { spring } from '../../lib/motion'
import { useTheme } from '../../lib/theme'
import { useAuth } from '../../lib/auth'
import { PageTransition } from '../motion'
import { Breadcrumbs } from './Nav'
import { IconButton } from './Button'
import { Drawer, Tooltip } from './Overlay'
import { PageSkeleton } from './Feedback'

export const NAV = [
  { to: '/app', label: 'Dashboard', short: 'Home', icon: LayoutDashboard, tone: 'var(--lavender)', end: true, bottom: true },
  { to: '/app/assess', label: 'Assessment', short: 'Assess', icon: ClipboardList, tone: 'var(--mint)', also: ['/app/result'], bottom: true },
  { to: '/app/explain', label: 'Explainability', short: 'Explain', icon: Brain, tone: 'var(--peach)', bottom: true },
  { to: '/app/forecast', label: 'Forecast', short: 'Forecast', icon: TrendingUp, tone: 'var(--sky)', bottom: true },
  { to: '/app/whatif', label: 'What-if', short: 'What-if', icon: FlaskConical, tone: 'var(--rose)', bottom: true },
  { to: '/app/performance', label: 'Performance', short: 'Models', icon: BarChart3, tone: 'var(--butter)' },
  { to: '/app/about', label: 'About', short: 'About', icon: Info, tone: 'var(--lavender)' },
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
    <Link to={to} className="brand" aria-label="FinSight AI home">
      <motion.span className="brand-mark" whileHover={{ rotate: -8, scale: 1.06 }} whileTap={{ scale: 0.92 }} transition={spring}>
        <LineChart size={20} aria-hidden="true" />
      </motion.span>
      <span className="brand-name">
        FinSight AI
        <span className="brand-sub">Financial profile &amp; forecasting</span>
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
        <strong style={{ display: 'block', color: 'var(--text)', marginBottom: 4 }}>Model</strong>
        {health ? (health.model_loaded ? `${health.model} loaded. Informational estimates, not financial advice.` : 'No trained model found - run scripts/train.py.') : 'Checking…'}
      </div>
    </aside>
  )
}

export function ThemeToggle() {
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
  const { user, logout } = useAuth()
  const state = healthError ? 'bad' : health ? '' : 'wait'
  return (
    <header className="topbar">
      <IconButton icon={Menu} label="Open navigation" className="menu-btn" onClick={onMenu} />
      <Brand />
      <span className="topbar-title">{title}</span>
      <span className="topbar-spacer" />
      <span className="status-pill" role="status" title={healthError ? 'API offline' : `Model: ${health?.model}`}>
        <span className={`status-dot ${state}`} aria-hidden="true" />
        <span className="status-text">{healthError ? 'API offline' : health ? `API online · ${health.model}` : 'Connecting…'}</span>
        <span className="sr-only">{healthError ? 'API offline' : health ? 'API online' : 'Connecting'}</span>
      </span>
      <span className="home-btn">
        <Tooltip content="Back to the landing page">
          <IconButton icon={Home} label="Landing page" onClick={() => navigate('/')} />
        </Tooltip>
      </span>
      <ThemeToggle />
      {user && (
        <>
          <span className="user-chip" title={user.email}>{user.name}</span>
          <Tooltip content="Sign out">
            <IconButton
              icon={LogOut}
              label="Sign out"
              onClick={() => {
                logout()
                navigate('/login', { replace: true })
              }}
            />
          </Tooltip>
        </>
      )}
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
  const current =
    [...NAV].reverse().find((n) => loc.pathname === n.to || loc.pathname.startsWith(`${n.to}/`) || n.also?.includes(loc.pathname)) || NAV[0]
  useEffect(() => {
    document.title = `${current.label} · FinSight AI`
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
                <Suspense fallback={<PageSkeleton />}>
                  <Outlet />
                </Suspense>
              </PageTransition>
            </AnimatePresence>
          </Container>
        </main>
      </div>
      <nav className="bottombar" aria-label="Quick navigation" style={{ gridTemplateColumns: `repeat(${NAV.filter((n) => n.bottom).length}, 1fr)` }}>
        {NAV.filter((n) => n.bottom).map((n) => (
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
