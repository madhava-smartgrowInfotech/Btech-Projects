import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import {
  BrainCircuit,
  Compass,
  Database,
  FlaskConical,
  HeartPulse,
  Home,
  Info,
  LayoutDashboard,
  Lightbulb,
  LineChart,
  LogOut,
  Menu,
  MoreHorizontal,
  Moon,
  Package,
  ShieldAlert,
  Sparkles,
  Stethoscope,
  Sun,
  UserRound,
} from 'lucide-react'
import { api } from '../../lib/api'
import { useAuth } from '../../lib/auth'
import { useAppState } from '../../lib/appstate'
import { spring } from '../../lib/motion'
import { useTheme } from '../../lib/theme'
import { PageTransition } from '../motion'
import { Breadcrumbs } from './Nav'
import { IconButton } from './Button'
import { Drawer, Tooltip } from './Overlay'

export const NAV_GROUPS = [
  {
    label: 'Overview',
    items: [{ to: '/app', label: 'Dashboard', short: 'Home', icon: LayoutDashboard, tone: 'var(--lavender)', end: true }],
  },
  {
    label: 'Data',
    items: [
      { to: '/app/data', label: 'Data upload', short: 'Data', icon: Database, tone: 'var(--mint)' },
      { to: '/app/eda', label: 'Exploration', short: 'Explore', icon: Compass, tone: 'var(--sky)' },
    ],
  },
  {
    label: 'Models',
    items: [
      { to: '/app/train', label: 'Model training', short: 'Train', icon: BrainCircuit, tone: 'var(--peach)' },
      { to: '/app/evaluation', label: 'Evaluation', short: 'Evaluate', icon: LineChart, tone: 'var(--rose)' },
      { to: '/app/monitoring', label: 'Monitoring', short: 'Monitor', icon: Stethoscope, tone: 'var(--butter)' },
    ],
  },
  {
    label: 'Customers',
    items: [
      { to: '/app/risk', label: 'Customer risk', short: 'Risk', icon: ShieldAlert, tone: 'var(--rose)' },
      { to: '/app/customer', label: 'Customer 360', short: '360', icon: UserRound, tone: 'var(--lavender)' },
      { to: '/app/explain', label: 'Explainable AI', short: 'Explain', icon: Sparkles, tone: 'var(--mint)' },
      { to: '/app/whatif', label: 'What-if', short: 'What-if', icon: FlaskConical, tone: 'var(--sky)' },
      { to: '/app/retention', label: 'Retention actions', short: 'Retain', icon: Lightbulb, tone: 'var(--butter)' },
      { to: '/app/batch', label: 'Batch prediction', short: 'Batch', icon: Package, tone: 'var(--peach)' },
    ],
  },
  {
    label: 'Help',
    items: [{ to: '/app/about', label: 'About project', short: 'About', icon: Info, tone: 'var(--lavender)' }],
  },
]
export const NAV = NAV_GROUPS.flatMap((g) => g.items)
const QUICK = ['/app', '/app/risk', '/app/customer', '/app/whatif']

export function Container({ children, className = '', style }) {
  return (
    <div className={`container ${className}`} style={style}>
      {children}
    </div>
  )
}

export function Brand({ to = '/' }) {
  return (
    <Link to={to} className="brand" aria-label="ChurnIQ home">
      <motion.span className="brand-mark" whileHover={{ rotate: -8, scale: 1.06 }} whileTap={{ scale: 0.92 }} transition={spring}>
        <HeartPulse size={22} aria-hidden="true" />
      </motion.span>
      <span className="brand-name">
        ChurnIQ
        <span className="brand-sub">Retention intelligence</span>
      </span>
    </Link>
  )
}

function NavItems({ onNavigate, layoutId = 'nav-pill' }) {
  return (
    <nav className="nav" aria-label="Main">
      {NAV_GROUPS.map((g) => (
        <div key={g.label} className="nav-group">
          <span className="nav-label">{g.label}</span>
          {g.items.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={onNavigate}>
              {({ isActive }) => (
                <>
                  {isActive && <motion.span layoutId={layoutId} className="nav-pill" transition={spring} />}
                  <motion.span className="nav-ico" style={{ background: n.tone, color: 'var(--on-pastel)' }} whileHover={{ scale: 1.1, rotate: -6 }} transition={spring}>
                    <n.icon size={16} aria-hidden="true" />
                  </motion.span>
                  <span>{n.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </div>
      ))}
    </nav>
  )
}

function StatusCard() {
  const { state } = useAppState()
  const ds = state?.dataset
  return (
    <div className="sidebar-foot" aria-live="polite">
      <div className="foot-row">
        <span className={`dot ${ds?.prepared ? 'on' : ''}`} aria-hidden="true" />
        <span>
          <strong>Dataset</strong>
          <small>{ds?.prepared ? `${ds.prepared_rows?.toLocaleString('en-IN')} customers ready` : ds?.loaded ? 'Loaded, not prepared' : 'None loaded yet'}</small>
        </span>
      </div>
      <div className="foot-row">
        <span className={`dot ${state?.model ? 'on' : ''}`} aria-hidden="true" />
        <span>
          <strong>Active model</strong>
          <small>{state?.model ? state.model.name : 'No model saved yet'}</small>
        </span>
      </div>
    </div>
  )
}

export function Sidebar() {
  return (
    <aside className="sidebar">
      <Brand />
      <NavItems />
      <StatusCard />
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
  const stateCls = healthError ? 'bad' : health ? '' : 'wait'
  return (
    <header className="topbar">
      <IconButton icon={Menu} label="Open navigation" className="menu-btn" onClick={onMenu} />
      <Brand />
      <span className="topbar-title">{title}</span>
      <span className="topbar-spacer" />
      <span className="status-pill" role="status">
        <span className={`status-dot ${stateCls}`} aria-hidden="true" />
        <span className="status-text">{healthError ? 'API offline' : health ? `API online${health.shap_available ? ' · SHAP' : ''}` : 'Connecting…'}</span>
        <span className="sr-only">{healthError ? 'API offline' : health ? 'API online' : 'Connecting'}</span>
      </span>
      <span className="home-btn">
        <Tooltip content="Back to the landing page">
          <IconButton icon={Home} label="Landing page" onClick={() => navigate('/')} />
        </Tooltip>
      </span>
      <ThemeToggle />
      <Tooltip content={user ? `Sign out ${user.email}` : 'Sign out'}>
        <IconButton
          icon={LogOut}
          label="Sign out"
          onClick={() => {
            logout()
            navigate('/login')
          }}
        />
      </Tooltip>
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
    document.title = `${current.label} · ChurnIQ`
    window.scrollTo(0, 0)
  }, [current.label])
  const quick = NAV.filter((n) => QUICK.includes(n.to))
  return (
    <div className="shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Sidebar />
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
        {quick.map((n) => (
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
        <button type="button" onClick={() => setOpen(true)} aria-label="More pages">
          <MoreHorizontal size={20} aria-hidden="true" />
          <span>More</span>
        </button>
      </nav>
      <Drawer open={open} onClose={() => setOpen(false)} title="Navigate">
        <NavItems onNavigate={() => setOpen(false)} layoutId="drawer-pill" />
        <StatusCard />
      </Drawer>
    </div>
  )
}

