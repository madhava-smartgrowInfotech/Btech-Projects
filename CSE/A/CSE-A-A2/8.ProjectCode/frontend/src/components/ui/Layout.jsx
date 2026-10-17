import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { Activity, BrainCircuit, Hospital, Home, LogIn, LogOut, Menu, Moon, SlidersHorizontal, Sun, Siren } from 'lucide-react'
import { useAuth } from '../../lib/auth'
import { useTheme } from '../../lib/theme'
import { Button, IconButton } from './Button'
import { Drawer } from './Feedback'
import { Badge } from './Display'
import { useToast } from './Toast'

export const APP_NAV = [
  { to: '/monitor', label: 'Live monitor', short: 'Monitor', icon: Activity },
  { to: '/manual', label: 'Manual override', short: 'Manual', icon: SlidersHorizontal },
  { to: '/response', label: 'Emergency response', short: 'Response', icon: Hospital },
]
const PUBLIC_NAV = [{ to: '/', label: 'Home', icon: Home, end: true }]

export function Container({ children, className = '', style }) {
  return (
    <div className={`container ${className}`} style={style}>
      {children}
    </div>
  )
}

export function Brand() {
  return (
    <Link to="/" className="brand" aria-label="ResQAI home">
      <span className="brand-mark" aria-hidden="true">
        <Siren size={20} strokeWidth={2.75} />
      </span>
      <span>ResQAI</span>
    </Link>
  )
}

export function ThemeToggle() {
  const { theme, toggle } = useTheme()
  return <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
}

/** Model status pill fed by /api/health. health: {status: 'loading'|'ok'|'error', models_loaded} */
export function ModelBadge({ health }) {
  if (health.status === 'loading') return <Badge>Checking…</Badge>
  if (health.status === 'error') return <Badge tone="blocked">API offline</Badge>
  return (
    <Badge tone={health.models_loaded ? 'pass' : 'upcoming'}>
      <BrainCircuit size={12} aria-hidden="true" />{' '}
      <span className="xs-long">{health.models_loaded ? 'ML models loaded' : 'Rule-based fallback'}</span>
      <span className="xs-short">{health.models_loaded ? 'ML' : 'Fallback'}</span>
    </Badge>
  )
}

function useSignOut() {
  const { signOut } = useAuth()
  const toast = useToast()
  const nav = useNavigate()
  return () => {
    signOut(true)
    toast.info('Signed out.')
    nav('/')
  }
}

function UserCard() {
  const { user } = useAuth()
  const signOut = useSignOut()
  if (!user) return null
  return (
    <div className="stack" style={{ '--gap': '10px' }}>
      <div className="card card-flat" style={{ padding: 12 }}>
        <strong style={{ display: 'block', overflowWrap: 'anywhere' }}>{user.name}</strong>
        <span className="tiny mono muted" style={{ overflowWrap: 'anywhere' }}>{user.email}</span>
      </div>
      <Button icon={LogOut} block onClick={signOut}>
        Sign out
      </Button>
    </div>
  )
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

export function Sidebar({ onNavigate, footer }) {
  return (
    <aside className="sidebar">
      <Brand />
      <div className="divider-label">Console</div>
      <NavList items={APP_NAV} onNavigate={onNavigate} />
      <div className="divider-label">Site</div>
      <NavList items={PUBLIC_NAV} onNavigate={onNavigate} />
      <div className="sidebar-foot">
        {footer}
        <UserCard />
      </div>
    </aside>
  )
}

export function Topbar({ title, onMenu, status }) {
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
      {status}
      <ThemeToggle />
    </header>
  )
}

/** App layout: sidebar + topbar + content; sidebar becomes a drawer + bottom bar on small screens. */
export function AppShell({ children, health, footer }) {
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  useEffect(() => setOpen(false), [loc.pathname])
  const current = APP_NAV.find((n) => loc.pathname.startsWith(n.to))
  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar footer={footer} />
      <div className="shell-main">
        <Topbar title={current ? `Console / ${current.label}` : 'Console'} onMenu={() => setOpen(true)} status={health && <ModelBadge health={health} />} />
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
          <NavList items={[...APP_NAV, ...PUBLIC_NAV]} onNavigate={() => setOpen(false)} />
          <UserCard />
        </div>
      </Drawer>
    </div>
  )
}

/** Public layout: topbar + content (landing page). */
export function PublicShell({ children, health }) {
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
        <IconButton icon={Menu} label="Open navigation" className="only-mobile" onClick={() => setOpen(true)} />
        <Brand />
        <span className="topbar-spacer" />
        <nav className="public-nav" aria-label="Main">
          {APP_NAV.map((n) => (
            <NavLink key={n.to} to={n.to}>
              {n.label}
            </NavLink>
          ))}
        </nav>
        {health && <span className="only-desktop"><ModelBadge health={health} /></span>}
        <ThemeToggle />
        {user ? (
          <Button size="sm" icon={LogOut} onClick={signOut} className="only-desktop">
            Sign out
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
          <NavList items={[...PUBLIC_NAV, ...APP_NAV]} onNavigate={() => setOpen(false)} />
          {user ? (
            <UserCard />
          ) : (
            <>
              <Button variant="primary" to="/login" icon={LogIn} block>
                Sign in
              </Button>
              <Button to="/register" block>
                Create account
              </Button>
            </>
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
