import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useOutlet } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Bean, BarChart3, Database, Droplets, FlaskConical, HeartPulse, Home, Info, LayoutDashboard, Menu, Moon, Stethoscope, Sun } from 'lucide-react'
import { useTheme } from '../../lib/theme'
import { useHealth } from '../../lib/health'
import { PageTransition } from '../motion'
import { IconButton } from './controls'
import { Badge } from './display'
import { Drawer, Tooltip } from './feedback'
import { Breadcrumbs } from './navigation'

export const NAV = [
  { to: '/app', label: 'Overview', icon: LayoutDashboard, end: true, group: 'Workspace' },
  { to: '/app/predict/diabetes', label: 'Diabetes', icon: Droplets, group: 'Predict risk' },
  { to: '/app/predict/heart', label: 'Heart disease', icon: HeartPulse, group: 'Predict risk' },
  { to: '/app/predict/liver', label: 'Liver disease', icon: FlaskConical, group: 'Predict risk' },
  { to: '/app/predict/kidney', label: 'Kidney disease', icon: Bean, group: 'Predict risk' },
  { to: '/app/models', label: 'Models', icon: BarChart3, group: 'Insights' },
  { to: '/app/data', label: 'Datasets', icon: Database, group: 'Insights' },
  { to: '/app/about', label: 'About', icon: Info, group: 'Insights' },
]
const GROUPS = [...new Set(NAV.map((n) => n.group))]

export function Container({ children, className = '' }) {
  return <div className={`container ${className}`}>{children}</div>
}

export function BrandMark({ size = 18 }) {
  return (
    <span className="brand-mark" aria-hidden="true">
      <Stethoscope size={size} strokeWidth={2.4} />
    </span>
  )
}

export function Sidebar({ onNavigate, pillId = 'nav-pill' }) {
  const { online, offline } = useHealth()
  return (
    <aside className="sidebar" aria-label="Main">
      <Link to="/" className="brand" onClick={onNavigate}>
        <BrandMark />
        <span>
          Health Assistant
          <small>Multi-disease prediction</small>
        </span>
      </Link>
      <nav aria-label="App sections" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {GROUPS.map((g) => (
          <div key={g} style={{ display: 'contents' }}>
            <div className="nav-label">{g}</div>
            {NAV.filter((n) => n.group === g).map(({ to, label, icon: Icon, end }) => (
              <NavLink key={to} to={to} end={end} className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`} onClick={onNavigate}>
                {({ isActive }) => (
                  <>
                    {isActive && <motion.span layoutId={pillId} className="nav-pill" transition={{ type: 'spring', stiffness: 400, damping: 34 }} />}
                    <Icon size={18} aria-hidden="true" />
                    <span>{label}</span>
                  </>
                )}
              </NavLink>
            ))}
          </div>
        ))}
        <div className="nav-label">Site</div>
        <NavLink to="/" end className="nav-link" onClick={onNavigate}>
          <Home size={18} aria-hidden="true" />
          <span>Landing page</span>
        </NavLink>
      </nav>
      <div className="sidebar-foot">
        <div className="faint" style={{ marginBottom: 4 }}>
          Prediction API
        </div>
        {offline ? (
          <Badge tone="danger" dot>
            Backend offline
          </Badge>
        ) : online ? (
          <Badge tone="safe" dot>
            Connected
          </Badge>
        ) : (
          <span className="faint">Checking…</span>
        )}
      </div>
    </aside>
  )
}

export function Topbar({ title, onMenu }) {
  const { theme, toggle } = useTheme()
  const { online, offline } = useHealth()
  return (
    <header className="topbar">
      <IconButton icon={Menu} label="Open navigation" className="menu-btn" onClick={onMenu} />
      <div className="topbar-title">{title}</div>
      <div className="topbar-spacer" />
      {offline ? (
        <Badge tone="danger" dot>
          Offline
        </Badge>
      ) : (
        online && (
          <span className="hide-sm">
            <Badge tone="safe" dot>
              API online
            </Badge>
          </span>
        )
      )}
      <Tooltip label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} placement="bottom">
        <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
      </Tooltip>
    </header>
  )
}

export function PageHeader({ crumbs, title, description, actions }) {
  return (
    <div className="page-header">
      <div style={{ minWidth: 0 }}>
        {crumbs && <Breadcrumbs items={crumbs} />}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  )
}

export function AppShell() {
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  const outlet = useOutlet()
  const current = [...NAV].reverse().find((n) => (n.end ? loc.pathname === n.to : loc.pathname.startsWith(n.to)))

  useEffect(() => {
    document.title = `${current ? current.label : 'App'} · Health Assistant`
    setOpen(false)
  }, [loc.pathname, current])

  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={current?.label || 'Health Assistant'} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          <AnimatePresence mode="wait" initial={false}>
            <PageTransition key={loc.pathname}>
              {outlet}
            </PageTransition>
          </AnimatePresence>
        </main>
      </div>
      <Drawer open={open} onClose={() => setOpen(false)} side="left" labelledBy="drawer-nav">
        <span id="drawer-nav" className="sr-only">
          Navigation
        </span>
        <Sidebar onNavigate={() => setOpen(false)} pillId="nav-pill-drawer" />
      </Drawer>
    </div>
  )
}
