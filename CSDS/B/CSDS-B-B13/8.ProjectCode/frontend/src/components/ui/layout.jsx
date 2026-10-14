import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useOutlet } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Home, LogOut, Menu, Moon, ScanSearch, Server, ShieldCheck, Sun } from 'lucide-react'
import { useTheme } from '../../lib/theme'
import { useAuth } from '../../auth'
import { PageTransition } from '../motion'
import { Button, IconButton } from './controls'
import { Drawer, Tooltip } from './feedback'
import { Breadcrumbs } from './navigation'

export const NAV = [
  { to: '/app/targets', label: 'Targets', icon: Server },
  { to: '/app/scans', label: 'Scans', icon: ScanSearch },
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

export function Sidebar({ onNavigate, pillId = 'nav-pill' }) {
  const { email, logout } = useAuth()
  return (
    <aside className="sidebar" aria-label="Main">
      <Link to="/" className="brand" onClick={onNavigate}>
        <BrandMark />
        <span>
          APISentry
          <small>Payment API security</small>
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
        <div className="faint break" style={{ marginBottom: 8 }}>
          {email}
        </div>
        <Button size="sm" variant="ghost" icon={LogOut} onClick={() => logout()}>
          Sign out
        </Button>
      </div>
    </aside>
  )
}

export function Topbar({ title, onMenu }) {
  const { theme, toggle } = useTheme()
  const label = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
  return (
    <header className="topbar">
      <IconButton icon={Menu} label="Open navigation" className="menu-btn" onClick={onMenu} />
      <div className="topbar-title">{title}</div>
      <div className="topbar-spacer" />
      <Tooltip label={label} placement="bottom">
        <IconButton icon={theme === 'dark' ? Sun : Moon} label={label} onClick={toggle} />
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
    document.title = `${current ? current.label : 'App'} · APISentry`
    setOpen(false)
  }, [loc.pathname, current])

  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={current?.label || 'APISentry'} onMenu={() => setOpen(true)} />
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
