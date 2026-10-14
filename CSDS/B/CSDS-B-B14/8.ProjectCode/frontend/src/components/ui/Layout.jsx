import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { BarChart3, Droplets, FlaskConical, Home, LayoutDashboard, LogOut, MapPinned, Menu, Moon, ShieldAlert, Sun, TrendingUp } from 'lucide-react'
import { useAuth } from '../../auth.jsx'
import { api } from '../../lib/api'
import { spring } from '../../lib/motion'
import { useTheme } from '../../lib/theme.jsx'
import { PageTransition } from '../motion'
import { Breadcrumbs } from './Nav'
import { Button, IconButton } from './Button'
import { Drawer, Tooltip } from './Overlay'

export const NAV = [
  { to: '/dashboard', label: 'Dashboard', short: 'Home', icon: LayoutDashboard, tone: 'var(--lavender)', end: true },
  { to: '/quality', label: 'Water quality', short: 'Quality', icon: FlaskConical, tone: 'var(--mint)' },
  { to: '/network', label: 'Network map', short: 'Network', icon: MapPinned, tone: 'var(--peach)' },
  { to: '/forecast', label: 'Demand forecast', short: 'Forecast', icon: TrendingUp, tone: 'var(--sky)' },
  { to: '/leaks', label: 'Leaks & anomalies', short: 'Leaks', icon: ShieldAlert, tone: 'var(--rose)' },
  { to: '/evaluation', label: 'Model evaluation', short: 'Models', icon: BarChart3, tone: 'var(--butter)' },
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
    <Link to={to} className="brand" aria-label="AquaVision home">
      <motion.span className="brand-mark" whileHover={{ rotate: -8, scale: 1.06 }} whileTap={{ scale: 0.92 }} transition={spring}>
        <Droplets size={20} aria-hidden="true" />
      </motion.span>
      <span className="brand-name">
        AquaVision
        <span className="brand-sub">Water utility intelligence</span>
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

function UserBlock() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  return (
    <div className="sidebar-foot">
      <strong style={{ display: 'block', color: 'var(--text)' }}>{user?.name}</strong>
      <span className="tiny muted" style={{ textTransform: 'capitalize' }}>
        {user?.role}
      </span>
      <div style={{ marginTop: 10 }}>
        <Button
          variant="secondary"
          size="sm"
          icon={LogOut}
          block
          onClick={() => {
            logout()
            navigate('/login')
          }}
        >
          Sign out
        </Button>
      </div>
    </div>
  )
}

export function Sidebar() {
  return (
    <aside className="sidebar">
      <Brand />
      <NavItems />
      <UserBlock />
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
  const text = healthError ? 'API offline' : health ? 'API online' : 'Connecting…'
  return (
    <header className="topbar">
      <IconButton icon={Menu} label="Open navigation" className="menu-btn" onClick={onMenu} />
      <Brand />
      <span className="topbar-title">{title}</span>
      <span className="topbar-spacer" />
      <span className="status-pill" role="status">
        <span className={`status-dot ${state}`} aria-hidden="true" />
        <span className="status-text">{text}</span>
        <span className="sr-only">{text}</span>
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
    document.title = `${current.label} · AquaVision`
    window.scrollTo(0, 0)
  }, [current.label])
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
        <UserBlock />
      </Drawer>
    </div>
  )
}
