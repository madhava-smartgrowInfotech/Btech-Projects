import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate, useOutlet } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { FileSearch, FolderOpen, GitCompareArrows, Home, Info, LayoutDashboard, Lightbulb, LogOut, Menu, Moon, ScanLine, Sun, TrendingUp, UploadCloud } from 'lucide-react'
import { useTheme } from '../../lib/theme'
import { useAuth } from '../../lib/auth'
import { PageTransition } from '../motion'
import { IconButton } from './controls'
import { Drawer, Tooltip } from './feedback'
import { Breadcrumbs } from './navigation'

export const NAV = [
  { to: '/app', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/app/upload', label: 'Upload report', icon: UploadCloud },
  { to: '/app/analysis', label: 'Report analysis', icon: FileSearch },
  { to: '/app/reports', label: 'My reports', icon: FolderOpen },
  { to: '/app/trends', label: 'Health trends', icon: TrendingUp },
  { to: '/app/compare', label: 'Compare reports', icon: GitCompareArrows },
  { to: '/app/insights', label: 'Health insights', icon: Lightbulb },
  { to: '/app/about', label: 'About', icon: Info },
]

export function Container({ children, className = '' }) {
  return <div className={`container ${className}`}>{children}</div>
}

export function BrandMark({ size = 18 }) {
  return (
    <span className="brand-mark" aria-hidden="true">
      <ScanLine size={size} strokeWidth={2.4} />
    </span>
  )
}

export function Sidebar({ onNavigate, pillId = 'nav-pill' }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  return (
    <aside className="sidebar" aria-label="Main">
      <Link to="/" className="brand" onClick={onNavigate}>
        <BrandMark />
        <span>
          LabLens
          <small>Lab report insights</small>
        </span>
      </Link>
      <nav aria-label="App sections" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div className="nav-label">Workspace</div>
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
        <div className="faint" style={{ marginBottom: 4 }}>
          Signed in as
        </div>
        <div style={{ fontWeight: 600, marginBottom: 10, overflowWrap: 'anywhere' }}>{user?.email}</div>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          style={{ width: '100%' }}
          onClick={() => {
            logout()
            onNavigate?.()
            navigate('/')
          }}
        >
          <LogOut size={15} aria-hidden="true" /> Sign out
        </button>
      </div>
    </aside>
  )
}

export function Topbar({ title, onMenu }) {
  const { theme, toggle } = useTheme()
  return (
    <header className="topbar">
      <IconButton icon={Menu} label="Open navigation" className="menu-btn" onClick={onMenu} />
      <div className="topbar-title">{title}</div>
      <div className="topbar-spacer" />
      <span className="hide-sm faint" style={{ fontSize: 12.5 }}>
        Educational tool - not a medical device
      </span>
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
  const current = NAV.find((n) => (n.end ? loc.pathname === n.to : loc.pathname.startsWith(n.to)))

  useEffect(() => {
    document.title = `${current ? current.label : 'App'} · LabLens`
    setOpen(false)
  }, [loc.pathname, current])

  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={current?.label || 'LabLens'} onMenu={() => setOpen(true)} />
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
