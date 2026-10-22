import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate, useOutlet } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Home, LayoutDashboard, Lock, LogOut, Menu, Moon, ScrollText, Share2, ShieldCheck, Sun, FolderLock } from 'lucide-react'
import { useTheme } from '../../lib/theme'
import { useAuth } from '../../lib/auth'
import { PageTransition } from '../motion'
import { Button, IconButton } from './controls'
import { Badge } from './display'
import { Drawer, Tooltip } from './feedback'
import { Breadcrumbs } from './navigation'

export const NAV = [
  { to: '/app', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/app/files', label: 'My files', icon: FolderLock },
  { to: '/app/shared', label: 'Shared with me', icon: Share2 },
  { to: '/app/audit', label: 'Audit log', icon: ScrollText },
  { to: '/app/security', label: 'Security', icon: ShieldCheck },
]

export function Container({ children, className = '' }) {
  return <div className={`container ${className}`}>{children}</div>
}

export function BrandMark({ size = 18 }) {
  return (
    <span className="brand-mark" aria-hidden="true">
      <Lock size={size} strokeWidth={2.4} />
    </span>
  )
}

function VaultState() {
  const { unlocked } = useAuth()
  return unlocked ? (
    <Badge tone="safe" dot>
      Vault unlocked
    </Badge>
  ) : (
    <Badge tone="warn" dot>
      Vault locked
    </Badge>
  )
}

export function Sidebar({ onNavigate, pillId = 'nav-pill' }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const out = async () => {
    onNavigate?.()
    await logout()
    navigate('/')
  }
  return (
    <aside className="sidebar" aria-label="Main">
      <Link to="/" className="brand" onClick={onNavigate}>
        <BrandMark />
        <span>
          CipherVault
          <small>Encrypted file storage</small>
        </span>
      </Link>
      <nav aria-label="App sections" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div className="nav-label">Vault</div>
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
        {user && (
          <>
            <div style={{ fontWeight: 600 }} className="break">
              {user.name}
            </div>
            <div className="faint break" style={{ marginBottom: 10 }}>
              {user.email}
            </div>
          </>
        )}
        <Button size="sm" variant="ghost" icon={LogOut} onClick={out}>
          Sign out
        </Button>
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
      <span className="hide-sm">
        <VaultState />
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
  const current = [...NAV].reverse().find((n) => (n.end ? loc.pathname === n.to : loc.pathname.startsWith(n.to)))

  useEffect(() => {
    document.title = `${current ? current.label : 'CipherVault'} · CipherVault`
    setOpen(false)
  }, [loc.pathname, current])

  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={current?.label || 'CipherVault'} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          <Container>
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

