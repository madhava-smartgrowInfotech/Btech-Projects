import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { BarChart3, BedDouble, LayoutDashboard, LogIn, LogOut, Menu, Moon, Stethoscope, Sun, Workflow } from 'lucide-react'
import { useAuth } from '../../lib/auth'
import { useTheme } from '../../lib/theme'
import { Button, IconButton } from './Button'
import { Drawer } from './Feedback'
import { useToast } from './Toast'

/* Adapted from the kit's Layout for HospiSense: navigation, brand and user card are this product's. */
export const APP_NAV = [
  { to: '/dashboard', label: 'Dashboard', short: 'Home', icon: LayoutDashboard, end: true },
  { to: '/admissions', label: 'Admissions', short: 'Admit', icon: Stethoscope },
  { to: '/forecasts', label: 'Forecasts', short: 'Forecast', icon: BedDouble },
  { to: '/allocation', label: 'Allocation', short: 'Plan', icon: Workflow },
  { to: '/performance', label: 'Model performance', short: 'Model', icon: BarChart3 },
]

const ROLE_LABEL = { admin: 'Administrator', doctor: 'Doctor' }

export function Container({ children, className = '', style }) {
  return (
    <div className={`container ${className}`} style={style}>
      {children}
    </div>
  )
}

export function Brand() {
  return (
    <Link to="/" className="brand" aria-label="HospiSense home">
      <span className="brand-mark" aria-hidden="true">
        ✚
      </span>
      <span>
        HOSPI
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
  return async () => {
    await logout()
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
      <div className="divider-label">Hospital operations</div>
      <NavList items={APP_NAV} onNavigate={onNavigate} />
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
      {user && <span className="badge only-desktop">{ROLE_LABEL[user.role] || user.role}</span>}
      <ThemeToggle />
    </header>
  )
}

/** Signed-in layout: sidebar + topbar + content; sidebar becomes a drawer and a bottom bar on small screens. */
export function AppShell({ children }) {
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  useEffect(() => setOpen(false), [loc.pathname])
  const current = APP_NAV.find((n) => (n.end ? loc.pathname === n.to : loc.pathname.startsWith(n.to)))
  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={current ? `HospiSense / ${current.label}` : 'HospiSense'} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          {children}
        </main>
      </div>
      <nav className="bottombar" aria-label="Quick navigation">
        {APP_NAV.map(({ to, short, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end}>
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

/** Public layout: topbar with section links, sign-in and a drawer on small screens. */
export function PublicShell({ children }) {
  const { user } = useAuth()
  const signOut = useSignOut()
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  useEffect(() => setOpen(false), [loc.pathname])
  const links = [
    { href: '#features', label: 'Features' },
    { href: '#how', label: 'How it works' },
  ]
  return (
    <>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <header className="topbar">
        <IconButton icon={Menu} label="Open navigation" className="only-mobile" onClick={() => setOpen(true)} />
        <Brand />
        <span className="topbar-spacer" />
        <nav className="public-nav" aria-label="Main">
          {links.map((l) => (
            <a key={l.href} href={l.href}>
              {l.label}
            </a>
          ))}
        </nav>
        <ThemeToggle />
        {user ? (
          <Button variant="primary" size="sm" to="/dashboard" icon={LayoutDashboard} className="only-desktop">
            Dashboard
          </Button>
        ) : (
          <Button variant="primary" size="sm" to="/login" icon={LogIn} className="only-desktop">
            Sign in
          </Button>
        )}
      </header>
      <main id="main" tabIndex={-1}>
        {children}
      </main>
      <Drawer open={open} onClose={() => setOpen(false)} title="Menu" side="left">
        <div className="stack">
          {links.map((l) => (
            <a key={l.href} href={l.href} className="nav-link" onClick={() => setOpen(false)}>
              {l.label}
            </a>
          ))}
          {user ? (
            <>
              <Button variant="primary" to="/dashboard" icon={LayoutDashboard} block>
                Dashboard
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
