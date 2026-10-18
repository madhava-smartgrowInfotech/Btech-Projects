import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate, useOutlet } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Bot, FileSearch, FlaskConical, Home, LayoutDashboard, LogOut, Menu, Moon, Network, ShieldCheck, Sun, Waves } from 'lucide-react'
import { useTheme } from '../../lib/theme'
import { useAuth } from '../../lib/auth'
import { useSimulation } from '../../hooks/useSimulation'
import { titleize } from '../../lib/format'
import { PageTransition } from '../motion'
import { IconButton } from './controls'
import { Badge } from './display'
import { Drawer, Tooltip } from './feedback'
import { Breadcrumbs } from './navigation'
import RunBar from '../safegrid/RunBar'

export const NAV = [
  { to: '/app', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/app/grid', label: 'Grid view', icon: Network },
  { to: '/app/agents', label: 'Agent monitor', icon: Bot },
  { to: '/app/shield', label: 'Safety shield', icon: ShieldCheck },
  { to: '/app/power-flow', label: 'Power flow', icon: Waves },
  { to: '/app/scenarios', label: 'Scenarios', icon: FlaskConical },
  { to: '/app/explain', label: 'Explainability', icon: FileSearch },
]

export function Container({ children, className = '' }) {
  return <div className={`container ${className}`}>{children}</div>
}

export function BrandMark({ size = 18 }) {
  return (
    <span className="brand-mark" aria-hidden="true">
      <ShieldCheck size={size} strokeWidth={2.4} />
    </span>
  )
}

const SOCKET_TONE = { open: 'safe', connecting: 'warn', closed: 'danger' }
const SOCKET_LABEL = { open: 'Live', connecting: 'Connecting', closed: 'Reconnecting' }

export function Sidebar({ onNavigate, pillId = 'nav-pill' }) {
  const { socket, status, error } = useSimulation()
  return (
    <aside className="sidebar" aria-label="Main">
      <Link to="/" className="brand" onClick={onNavigate}>
        <BrandMark />
        <span>
          SafeGrid-AI
          <small>Shielded multi-agent grid control</small>
        </span>
      </Link>
      <nav aria-label="Console sections" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div className="nav-label">Console</div>
        {NAV.map(({ to, label, icon: Icon, end }) => (
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
        <div className="nav-label">Site</div>
        <NavLink to="/" end className="nav-link" onClick={onNavigate}>
          <Home size={18} aria-hidden="true" />
          <span>Landing page</span>
        </NavLink>
      </nav>
      <div className="sidebar-foot">
        <div className="faint" style={{ marginBottom: 6 }}>
          Live stream
        </div>
        {error ? (
          <Badge tone="danger" dot>
            Backend offline
          </Badge>
        ) : (
          <Badge tone={SOCKET_TONE[socket] || 'neutral'} dot>
            {SOCKET_LABEL[socket] || socket}
          </Badge>
        )}
        <div className="faint" style={{ marginTop: 10 }}>
          Agent brain
        </div>
        <div style={{ fontWeight: 600 }}>{status?.provider?.provider ? titleize(status.provider.provider) : '-'}</div>
      </div>
    </aside>
  )
}

export function Topbar({ title, onMenu }) {
  const { theme, toggle } = useTheme()
  const { user, logout } = useAuth()
  const { status, error } = useSimulation()
  const nav = useNavigate()
  const running = status?.status === 'running'
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
        status && (
          <span className="hide-sm">
            <Badge tone={running ? 'safe' : 'neutral'} dot>
              {titleize(status.status)} · {status.time}
            </Badge>
          </span>
        )
      )}
      <Tooltip label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} placement="bottom">
        <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
      </Tooltip>
      {user && (
        <>
          <span className="user-chip hide-sm" title={user.role}>
            <span className="user-avatar" aria-hidden="true">
              {user.name.slice(0, 1)}
            </span>
            {user.name}
          </span>
          <Tooltip label="Sign out" placement="bottom">
            <IconButton
              icon={LogOut}
              label="Sign out"
              onClick={() => {
                logout()
                nav('/login', { replace: true })
              }}
            />
          </Tooltip>
        </>
      )}
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
  const current = [...NAV].reverse().find((n) => (n.end ? loc.pathname.replace(/\/$/, '') === n.to : loc.pathname.startsWith(n.to)))

  useEffect(() => {
    document.title = `${current ? current.label : 'Console'} · SafeGrid-AI`
    setOpen(false)
  }, [loc.pathname, current])

  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={current?.label || 'SafeGrid-AI'} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          <Container>
            <RunBar />
            <AnimatePresence mode="wait" initial={false}>
              <PageTransition key={loc.pathname}>{outlet}</PageTransition>
            </AnimatePresence>
          </Container>
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
