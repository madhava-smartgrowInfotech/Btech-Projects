import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { Activity, BarChart3, ListOrdered, LogIn, LogOut, Menu, Moon, PlusSquare, Sun } from 'lucide-react'
import { useAuth } from '../../lib/auth'
import { useTheme } from '../../lib/theme'
import { Button, IconButton } from './Button'
import { Drawer } from './Feedback'
import { useToast } from './Toast'

export const APP_NAV = [
  { to: '/app/queue', label: 'Triage queue', short: 'Queue', icon: ListOrdered },
  { to: '/app/new', label: 'New patient', short: 'New', icon: PlusSquare },
  { to: '/app/performance', label: 'Performance', short: 'Metrics', icon: BarChart3 },
]

export function Container({ children, className = '', style }) {
  return (
    <div className={`container ${className}`} style={style}>
      {children}
    </div>
  )
}

export function Brand() {
  return (
    <Link to="/" className="brand" aria-label="ATHENA home">
      <span className="brand-mark" aria-hidden="true">
        <Activity size={20} strokeWidth={3} />
      </span>
      <span>ATHENA</span>
    </Link>
  )
}

export function ThemeToggle() {
  const { theme, toggle } = useTheme()
  return <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
}

function useSignOut() {
  const { logout } = useAuth()
  const toast = useToast()
  const nav = useNavigate()
  return () => {
    logout()
    toast.info('Signed out.')
    nav('/')
  }
}

function NavList({ items, onNavigate }) {
  return (
    <nav className="sidebar-nav" aria-label="Main">
      {items.map(({ to, label, icon: Icon, end }) => (
        <NavLink key={to} to={to} end={end} className="nav-link" onClick={onNavigate}>
          <Icon size={20} aria-hidden="true" />
          {label}
        </NavLink>
      ))}
    </nav>
  )
}

export function Sidebar({ onNavigate }) {
  const { user } = useAuth()
  const signOut = useSignOut()
  return (
    <aside className="sidebar">
      <Brand />
      <div className="divider-label">Emergency dept.</div>
      <NavList items={APP_NAV} onNavigate={onNavigate} />
      <div className="sidebar-foot">
        {user && (
          <div className="card card-flat" style={{ padding: 12 }}>
            <strong style={{ display: 'block', overflowWrap: 'anywhere' }}>{user.name}</strong>
            <span className="tiny mono muted" style={{ textTransform: 'capitalize' }}>
              {user.role}
            </span>
          </div>
        )}
        <Button icon={LogOut} block onClick={signOut}>
          Sign out
        </Button>
      </div>
    </aside>
  )
}

export function Topbar({ title, onMenu }) {
  const { user } = useAuth()
  return (
    <header className="topbar">
      {onMenu && <IconButton icon={Menu} label="Open navigation" className="only-mobile" onClick={onMenu} />}
      <span className="only-mobile">
        <Brand />
      </span>
      {title && <span className="topbar-title only-desktop">{title}</span>}
      <span className="topbar-spacer" />
      {user && <span className="badge only-desktop">{user.name}</span>}
      <ThemeToggle />
    </header>
  )
}

/** Signed-in layout: sidebar + topbar + content; sidebar becomes a drawer plus a bottom bar on small screens. */
export function AppShell({ children }) {
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  useEffect(() => setOpen(false), [loc.pathname])
  const current = APP_NAV.find((n) => loc.pathname.startsWith(n.to)) || (loc.pathname.startsWith('/app/patients') ? { label: 'Patient result' } : null)
  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={current ? `ATHENA / ${current.label}` : 'ATHENA'} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          {children}
        </main>
      </div>
      <nav className="bottombar" aria-label="Quick navigation">
        {APP_NAV.map(({ to, short, icon: Icon }) => (
          <NavLink key={to} to={to}>
            <Icon size={20} aria-hidden="true" />
            {short}
          </NavLink>
        ))}
      </nav>
      <Drawer open={open} onClose={() => setOpen(false)} title="Menu" side="left">
        <div className="stack">
          <NavList items={APP_NAV} onNavigate={() => setOpen(false)} />
        </div>
      </Drawer>
    </div>
  )
}

/** Landing / login layout: topbar with brand, theme toggle and the main call to action. */
export function PublicShell({ children }) {
  const { user } = useAuth()
  const signOut = useSignOut()
  return (
    <>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <header className="topbar">
        <Brand />
        <span className="topbar-spacer" />
        <ThemeToggle />
        {user ? (
          <>
            <Button variant="primary" size="sm" to="/app/queue" icon={ListOrdered}>
              Open queue
            </Button>
            <Button size="sm" icon={LogOut} onClick={signOut} className="only-desktop">
              Sign out
            </Button>
          </>
        ) : (
          <Button variant="primary" size="sm" to="/login" icon={LogIn}>
            Sign in
          </Button>
        )}
      </header>
      <main id="main" tabIndex={-1}>
        {children}
      </main>
    </>
  )
}

export function PageHeader({ eyebrow, title, description, actions, crumbs }) {
  return (
    <header className="page-header">
      <div style={{ minWidth: 0 }}>
        {crumbs}
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h1 style={{ marginTop: eyebrow ? 10 : 0, overflowWrap: 'anywhere' }}>{title}</h1>
        {description && <p className="desc">{description}</p>}
      </div>
      {actions && <div className="row">{actions}</div>}
    </header>
  )
}
