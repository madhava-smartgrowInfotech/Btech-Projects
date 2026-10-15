import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate, useOutlet } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { BarChart3, Brain, Dna, Fingerprint, Gauge, History, Home, LogOut, Menu, Moon, Sun } from 'lucide-react'
import { useTheme } from '../../lib/theme'
import { useAuth } from '../../lib/auth'
import { useHealth } from '../../lib/health'
import { PageTransition } from '../motion'
import { IconButton } from './controls'
import { Badge } from './display'
import { Drawer, Tooltip } from './feedback'
import { Breadcrumbs } from './navigation'

export const NAV = [
  { to: '/app/mri', label: 'MRI analysis', icon: Brain },
  { to: '/app/label-efficiency', label: 'Label efficiency', icon: BarChart3 },
  { to: '/app/dna', label: 'DNA analysis', icon: Dna },
  { to: '/app/str', label: 'STR matching', icon: Fingerprint },
  { to: '/app/performance', label: 'Model performance', icon: Gauge },
  { to: '/app/history', label: 'History', icon: History },
]

export function Container({ children, className = '' }) {
  return <div className={`container ${className}`}>{children}</div>
}

export function BrandMark({ size = 18 }) {
  return (
    <span className="brand-mark" aria-hidden="true">
      <Dna size={size} strokeWidth={2.4} />
    </span>
  )
}

export function ApiBadge() {
  const { online } = useHealth()
  if (online === undefined) return null
  return (
    <Badge tone={online ? 'safe' : 'danger'} dot>
      {online ? 'API online' : 'API offline'}
    </Badge>
  )
}

export function Sidebar({ onNavigate, pillId = 'nav-pill' }) {
  const { user } = useAuth()
  return (
    <aside className="sidebar" aria-label="Main">
      <Link to="/" className="brand" onClick={onNavigate}>
        <BrandMark />
        <span>
          BioSight
          <small>JEPA imaging &amp; DNA</small>
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
        <div className="faint" style={{ marginBottom: 4 }}>
          Signed in as
        </div>
        <div style={{ fontWeight: 600 }} className="break">
          {user?.name || '-'}
        </div>
        <div className="faint break">{user?.email}</div>
      </div>
    </aside>
  )
}

export function Topbar({ title, onMenu }) {
  const { theme, toggle } = useTheme()
  const { logout } = useAuth()
  const navigate = useNavigate()
  const dark = theme === 'dark'
  return (
    <header className="topbar">
      <IconButton icon={Menu} label="Open navigation" className="menu-btn" onClick={onMenu} />
      <div className="topbar-title">{title}</div>
      <div className="topbar-spacer" />
      <span className="hide-sm">
        <ApiBadge />
      </span>
      <Tooltip label={dark ? 'Switch to light mode' : 'Switch to dark mode'} placement="bottom">
        <IconButton icon={dark ? Sun : Moon} label={dark ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
      </Tooltip>
      <Tooltip label="Sign out" placement="bottom">
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
    document.title = `${current ? current.label : 'App'} · BioSight`
    setOpen(false)
  }, [loc.pathname, current])

  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={current?.label || 'BioSight'} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          <AnimatePresence mode="wait" initial={false}>
            <PageTransition key={loc.pathname}>{outlet}</PageTransition>
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
