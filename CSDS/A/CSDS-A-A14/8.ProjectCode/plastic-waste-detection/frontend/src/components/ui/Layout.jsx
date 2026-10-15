import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Home, Info, LayoutDashboard, LineChart, Menu, Moon, ScanSearch, Sun, Waves } from 'lucide-react'
import { useHealth } from '../../lib/health'
import { spring } from '../../lib/motion'
import { useTheme } from '../../lib/theme'
import { PageTransition } from '../motion'
import { Breadcrumbs } from './Nav'
import { IconButton } from './Button'
import { Drawer, Tooltip } from './Overlay'

export const NAV = [
  { to: '/app/detect', label: 'Detection', short: 'Detect', icon: ScanSearch, tone: 'var(--lavender)' },
  { to: '/app/dashboard', label: 'Dashboard', short: 'Stats', icon: LayoutDashboard, tone: 'var(--mint)' },
  { to: '/app/evaluation', label: 'Evaluation', short: 'Eval', icon: LineChart, tone: 'var(--peach)' },
  { to: '/app/about', label: 'About', short: 'About', icon: Info, tone: 'var(--sky)' },
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
    <Link to={to} className="brand" aria-label="PlastiScan home">
      <motion.span className="brand-mark" whileHover={{ rotate: -8, scale: 1.06 }} whileTap={{ scale: 0.92 }} transition={spring}>
        <Waves size={22} aria-hidden="true" />
      </motion.span>
      <span className="brand-name">
        PlastiScan
        <span className="brand-sub">Ocean plastic detection</span>
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

/** Short, honest description of the loaded model for the sidebar / status pill. */
export function modelLabel(health) {
  const m = health?.model
  if (!m) return null
  if (m.status === 'error') return 'Model failed to load'
  if (!m.ready) return 'Loading model…'
  return m.used_fallback ? 'COCO placeholder model' : 'Trained plastic model'
}

export function Sidebar({ health }) {
  return (
    <aside className="sidebar">
      <Brand />
      <NavItems />
      <div className="sidebar-foot">
        <strong style={{ display: 'block', color: 'var(--text)', marginBottom: 4 }}>Model</strong>
        {health ? `${modelLabel(health)} · ${health.device.toUpperCase()}` : 'Checking…'}
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
  const state = healthError ? 'bad' : health ? (health.model?.status === 'error' ? 'bad' : health.model?.ready ? '' : 'wait') : 'wait'
  const text = healthError ? 'API offline' : health ? `API online · ${health.device.toUpperCase()}` : 'Connecting…'
  return (
    <header className="topbar">
      <IconButton icon={Menu} label="Open navigation" className="menu-btn" onClick={onMenu} />
      <Brand />
      <span className="topbar-title">{title}</span>
      <span className="topbar-spacer" />
      <span className="status-pill" role="status" title={healthError ? 'API offline' : modelLabel(health) || undefined}>
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

export function AppShell() {
  const loc = useLocation()
  const [open, setOpen] = useState(false)
  const health = useHealth()
  const current = [...NAV].reverse().find((n) => loc.pathname === n.to || loc.pathname.startsWith(`${n.to}/`)) || NAV[0]
  useEffect(() => {
    document.title = `${current.label} · PlastiScan`
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
