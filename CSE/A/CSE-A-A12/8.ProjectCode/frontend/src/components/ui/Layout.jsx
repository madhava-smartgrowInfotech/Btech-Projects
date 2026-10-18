import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { BookOpen, History, LayoutDashboard, LogIn, LogOut, Menu, Moon, ScanLine, Sun } from 'lucide-react'
import { useAuth } from '../../lib/auth'
import { useHealth } from '../../lib/hooks'
import { useTheme } from '../../lib/theme'
import { Badge } from './Display'
import { Button, IconButton } from './Button'
import { Drawer } from './Feedback'
import { useToast } from './Toast'

export const APP_NAV = [
  { to: '/app', label: 'Dashboard', short: 'Home', icon: LayoutDashboard, end: true },
  { to: '/app/detect', label: 'New scan', short: 'Scan', icon: ScanLine },
  { to: '/app/history', label: 'History', short: 'History', icon: History },
  { to: '/app/about', label: 'About', short: 'About', icon: BookOpen },
]

const DISCLAIMER = 'Academic prototype for computer-aided screening support. Not a certified medical device and not a substitute for professional diagnosis.'

export function Disclaimer({ className = '' }) {
  return <p className={`tiny muted no-print ${className}`}>{DISCLAIMER}</p>
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
    <Link to="/" className="brand" aria-label="PneumoDetect home">
      <span className="brand-mark" aria-hidden="true">
        ✚
      </span>
      <span>
        PNEUMO
        <br />
        DETECT
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

/** Shown wherever the model is not a trained one, so nobody mistakes demo output for a diagnosis. */
export function ModelBadge() {
  const health = useHealth()
  if (!health?.model_ready) return health ? <Badge tone="info">Model loading…</Badge> : null
  return health.demo_mode ? <Badge tone="upcoming">Demo model</Badge> : <Badge tone="pass">Trained model</Badge>
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
            <span className="tiny mono muted">{user.role}</span>
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
      <ModelBadge />
      {user && <span className="badge only-desktop">{user.email}</span>}
      <ThemeToggle />
    </header>
  )
}

/** Signed-in layout: sidebar + topbar + content; sidebar becomes a drawer + bottom bar on small screens. */
export function AppShell({ children }) {
  const [open, setOpen] = useState(false)
  const signOut = useSignOut()
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
        <Topbar title={current ? `Workspace / ${current.label}` : 'Workspace'} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          {children}
          <Disclaimer className="app-disclaimer" />
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
          <Button icon={LogOut} block onClick={signOut}>
            Sign out
          </Button>
        </div>
      </Drawer>
    </div>
  )
}

const PUBLIC_NAV = [
  { to: '/#how', label: 'How it works' },
  { to: '/#classes', label: 'Classes' },
]

/** Public layout (landing, sign-in): topbar with nav + content + footer. */
export function PublicShell({ children }) {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  useEffect(() => setOpen(false), [loc.pathname, loc.hash])
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
          {PUBLIC_NAV.map((n) => (
            <a key={n.to} href={n.to}>
              {n.label}
            </a>
          ))}
        </nav>
        <ModelBadge />
        <ThemeToggle />
        {user ? (
          <Button variant="primary" size="sm" to="/app" icon={LayoutDashboard} className="only-desktop">
            Open app
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
      {loc.pathname !== '/' && (
        <Container style={{ paddingBottom: 32 }}>
          <Disclaimer />
        </Container>
      )}
      <Drawer open={open} onClose={() => setOpen(false)} title="Menu" side="left">
        <div className="stack">
          {PUBLIC_NAV.map((n) => (
            <a key={n.to} href={n.to} className="nav-link" onClick={() => setOpen(false)}>
              {n.label}
            </a>
          ))}
          <Button variant="primary" to={user ? '/app' : '/login'} icon={user ? LayoutDashboard : LogIn} block>
            {user ? 'Open app' : 'Sign in'}
          </Button>
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
