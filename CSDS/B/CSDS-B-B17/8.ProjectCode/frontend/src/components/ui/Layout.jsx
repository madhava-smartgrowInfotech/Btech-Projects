import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { AudioLines, BarChart3, FlaskConical, Gauge, LayoutDashboard, LogIn, LogOut, Menu, Moon, PhoneCall, Sun } from 'lucide-react'
import { useAuth } from '../../lib/auth'
import { useTheme } from '../../lib/theme'
import { Button, IconButton } from './Button'
import { Drawer } from './Feedback'
import { useToast } from './Toast'

export const APP_NAV = [
  { to: '/calls', label: 'Calls', short: 'Calls', icon: PhoneCall },
  { to: '/studio', label: 'Sample studio', short: 'Studio', icon: FlaskConical },
  { to: '/analytics', label: 'Analytics', short: 'Stats', icon: BarChart3 },
  { to: '/performance', label: 'Model performance', short: 'Models', icon: Gauge },
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
    <Link to="/" className="brand" aria-label="CallSense home">
      <span className="brand-mark" aria-hidden="true">
        <AudioLines size={20} strokeWidth={3} />
      </span>
      <span>
        CALL
        <br />
        SENSE
      </span>
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
    nav('/') // leave the guarded area first, otherwise RequireAuth redirects to /login
    logout()
    toast.info('Signed out.')
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
      <div className="divider-label">Workspace</div>
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
      {user && (
        <span className="badge only-desktop">
          {user.name} · {user.role}
        </span>
      )}
      <ThemeToggle />
    </header>
  )
}

/** Signed-in layout: sidebar + topbar + content; sidebar becomes a drawer + bottom bar on small screens. */
export function AppShell({ children }) {
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  const signOut = useSignOut()
  useEffect(() => setOpen(false), [loc.pathname])
  const current = APP_NAV.find((n) => loc.pathname.startsWith(n.to))
  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={current ? `CallSense / ${current.label}` : 'CallSense'} onMenu={() => setOpen(true)} />
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
          <Button icon={LogOut} block onClick={signOut}>
            Sign out
          </Button>
        </div>
      </Drawer>
    </div>
  )
}

/** Public layout (landing, login): topbar + content. */
export function PublicShell({ children }) {
  const { user } = useAuth()
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
          <Button variant="primary" size="sm" to="/calls" icon={LayoutDashboard}>
            Open dashboard
          </Button>
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
