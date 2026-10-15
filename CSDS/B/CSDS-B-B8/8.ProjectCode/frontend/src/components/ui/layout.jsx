import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useOutlet } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Activity, BarChart3, Bell, CalendarDays, HeartPulse, Home, LogOut, Menu, Moon, Sun, Users } from 'lucide-react'
import { useTheme } from '../../lib/theme'
import { useAuth } from '../../lib/auth'
import { useMonitor } from '../../lib/monitor'
import { PageTransition } from '../motion'
import FallOverlay from '../care/FallOverlay'
import { IconButton } from './controls'
import { Badge } from './display'
import { Drawer, Tooltip } from './feedback'
import { Breadcrumbs } from './navigation'

export const NAV = [
  { to: '/app/monitor', label: 'Live monitor', icon: Activity },
  { to: '/app/alerts', label: 'Alerts', icon: Bell },
  { to: '/app/contacts', label: 'Contacts & settings', icon: Users },
  { to: '/app/report', label: 'Daily report', icon: CalendarDays },
  { to: '/app/performance', label: 'Model performance', icon: BarChart3 },
]

export function Container({ children, className = '' }) {
  return <div className={`container ${className}`}>{children}</div>
}

export function BrandMark({ size = 18 }) {
  return (
    <span className="brand-mark" aria-hidden="true">
      <HeartPulse size={size} strokeWidth={2.4} />
    </span>
  )
}

function MonitorStatus() {
  const { state, error } = useMonitor()
  if (error) {
    return (
      <Badge tone="danger" dot>
        Backend offline
      </Badge>
    )
  }
  if (!state) return <span className="faint">Connecting…</span>
  return state.running ? (
    <Badge tone="safe" dot>
      Monitoring · {state.fps} fps
    </Badge>
  ) : (
    <Badge dot>Monitoring stopped</Badge>
  )
}

export function Sidebar({ onNavigate, pillId = 'nav-pill' }) {
  return (
    <aside className="sidebar" aria-label="Main">
      <Link to="/" className="brand" onClick={onNavigate}>
        <BrandMark />
        <span>
          CareWatch
          <small>Fall detection &amp; alerts</small>
        </span>
      </Link>
      <nav aria-label="App sections" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div className="nav-label">Workspace</div>
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`} onClick={onNavigate}>
            {({ isActive }) => (
              <>
                {isActive && <motion.span layoutId={pillId} className="nav-pill" transition={{ type: 'spring', stiffness: 400, damping: 34 }} />}
                <Icon size={18} aria-hidden="true" />
                <span>{label}</span>
              </>
            )}
          </NavLink>
        ))}
        <div className="nav-label">Site</div>
        <NavLink to="/" end className="nav-link" onClick={onNavigate}>
          <Home size={18} aria-hidden="true" />
          <span>Landing page</span>
        </NavLink>
      </nav>
      <div className="sidebar-foot">
        <div className="faint" style={{ marginBottom: 6 }}>
          Camera
        </div>
        <MonitorStatus />
      </div>
    </aside>
  )
}

export function Topbar({ title, onMenu }) {
  const { theme, toggle } = useTheme()
  const { user, signOut } = useAuth()
  const { state, error } = useMonitor()
  const darkLabel = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
  return (
    <header className="topbar">
      <IconButton icon={Menu} label="Open navigation" className="menu-btn" onClick={onMenu} />
      <div className="topbar-title">{title}</div>
      <div className="topbar-spacer" />
      {error ? (
        <Badge tone="danger" dot>
          Offline
        </Badge>
      ) : (
        state?.running && (
          <span className="hide-sm">
            <Badge tone={state.fall_state === 'normal' ? 'safe' : 'danger'} dot>
              {state.fall_state === 'normal' ? 'Live' : 'Fall check'}
            </Badge>
          </span>
        )
      )}
      {user && (
        <span className="hide-sm faint" title={user.email}>
          {user.name}
        </span>
      )}
      <Tooltip label={darkLabel} placement="bottom">
        <IconButton icon={theme === 'dark' ? Sun : Moon} label={darkLabel} onClick={toggle} />
      </Tooltip>
      <Tooltip label="Sign out" placement="bottom">
        <IconButton icon={LogOut} label="Sign out" onClick={signOut} />
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
  const current = NAV.find((n) => loc.pathname.startsWith(n.to))

  useEffect(() => {
    document.title = `${current ? current.label : 'App'} · CareWatch`
    setOpen(false)
  }, [loc.pathname, current])

  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={current?.label || 'CareWatch'} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          <AnimatePresence mode="wait" initial={false}>
            <PageTransition key={loc.pathname}>
              <Container>{outlet}</Container>
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
      <FallOverlay />
    </div>
  )
}
