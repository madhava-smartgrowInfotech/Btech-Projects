import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { BarChart3, LayoutDashboard, LogIn, LogOut, Menu, Moon, ScanLine, ShieldCheck, Sun, Users } from 'lucide-react'
import { useAuth } from '../../lib/auth'
import { useTheme } from '../../lib/theme'
import { Button, IconButton } from './Button'
import { Drawer } from './Feedback'
import { useToast } from './Toast'

// PulmoVision adaptation of the kit shell: navigation and roles follow this product's screens.
export const APP_NAV = [
  { to: '/scan', label: 'New scan', short: 'Scan', icon: ScanLine },
  { to: '/patients', label: 'Patients', short: 'Patients', icon: Users },
  { to: '/performance', label: 'Model performance', short: 'Models', icon: BarChart3 },
  { to: '/audit', label: 'Audit log', short: 'Audit', icon: ShieldCheck, doctorOnly: true },
]

const ROLE_LABEL = { doctor: 'Doctor', technician: 'Technician' }

export function appNavFor(user) {
  return APP_NAV.filter((n) => !n.doctorOnly || user?.role === 'doctor')
}

export function Container({ children, className = '', style }) {
  return (
    <div className={`container ${className}`} style={style}>
      {children}
    </div>
  )
}

export function Brand() {
  return (
    <Link to="/" className="brand" aria-label="PulmoVision home">
      <img src="/favicon.svg" alt="" width="28" height="28" aria-hidden="true" />
      <span>
        PULMO
        <br />
        VISION
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
  return async () => {
    await logout()
    toast.info('Signed out.')
    nav('/login')
  }
}

function NavList({ items, onNavigate }) {
  return (
    <nav className="sidebar-nav" aria-label="Main">
      {items.map(({ to, label, icon: Icon }) => (
        <NavLink key={to} to={to} className="nav-link" onClick={onNavigate}>
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
      <NavList items={appNavFor(user)} onNavigate={onNavigate} />
      <div className="sidebar-foot">
        {user && (
          <div className="card card-flat" style={{ padding: 12 }}>
            <strong style={{ display: 'block', overflowWrap: 'anywhere' }}>{user.name}</strong>
            <span className="tiny mono muted">{ROLE_LABEL[user.role] || user.role}</span>
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

/** Signed-in layout: sidebar + topbar + content; sidebar becomes a drawer and a bottom bar on small screens. */
export function AppShell({ title, children }) {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  useEffect(() => setOpen(false), [loc.pathname])
  const items = appNavFor(user)
  const current = items.find((n) => loc.pathname.startsWith(n.to))
  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={title || (current ? current.label : '')} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          {children}
        </main>
      </div>
      <nav className="bottombar" aria-label="Quick navigation">
        {items.map(({ to, short, icon: Icon }) => (
          <NavLink key={to} to={to}>
            <Icon size={20} aria-hidden="true" />
            {short}
          </NavLink>
        ))}
      </nav>
      <Drawer open={open} onClose={() => setOpen(false)} title="Menu" side="left">
        <div className="stack">
          <NavList items={items} onNavigate={() => setOpen(false)} />
        </div>
      </Drawer>
    </div>
  )
}

/** Public layout (landing, sign in): topbar with actions + content. */
export function PublicShell({ children }) {
  const { user } = useAuth()
  const signOut = useSignOut()
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  useEffect(() => setOpen(false), [loc.pathname])
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
            <Button variant="primary" size="sm" to="/scan" icon={ScanLine} className="only-desktop">
              Open workspace
            </Button>
            <Button size="sm" icon={LogOut} onClick={signOut} className="only-desktop">
              Sign out
            </Button>
          </>
        ) : (
          <Button variant="primary" size="sm" to="/login" icon={LogIn} className="only-desktop">
            Sign in
          </Button>
        )}
        <IconButton icon={Menu} label="Open menu" className="only-mobile" onClick={() => setOpen(true)} />
      </header>
      <main id="main" tabIndex={-1}>
        {children}
      </main>
      <Drawer open={open} onClose={() => setOpen(false)} title="Menu" side="right">
        <div className="stack">
          {user ? (
            <>
              <Button variant="primary" to="/scan" icon={LayoutDashboard} block>
                Open workspace
              </Button>
              <Button icon={LogOut} block onClick={signOut}>
                Sign out
              </Button>
            </>
          ) : (
            <Button variant="primary" to="/login" icon={LogIn} block>
              Sign in
            </Button>
          )}
        </div>
      </Drawer>
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
