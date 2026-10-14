import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { BookOpen, LayoutDashboard, ListChecks, LogIn, LogOut, Menu, Moon, PlusSquare, ScanFace, Sun, Users } from 'lucide-react'
import { useAuth } from '../../lib/auth'
import { useTheme } from '../../lib/theme'
import { Button, IconButton } from './Button'
import { Drawer } from './Feedback'
import { useToast } from './Toast'

export const FACULTY_NAV = [
  { to: '/app', label: 'Dashboard', short: 'Home', icon: LayoutDashboard, end: true },
  { to: '/app/sessions', label: 'Sessions', short: 'Sessions', icon: ListChecks, end: true },
  { to: '/app/sessions/new', label: 'New session', short: 'New', icon: PlusSquare },
  { to: '/app/students', label: 'Students', short: 'Students', icon: Users },
]
const PUBLIC_NAV = [
  { to: '/about', label: 'How it works', icon: BookOpen },
  { to: '/checkin', label: 'Student check-in', icon: ScanFace },
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
    <Link to="/" className="brand" aria-label="Attendance Magic home">
      <span className="brand-mark" aria-hidden="true">
        ✦
      </span>
      <span>
        ATTENDANCE
        <br />
        MAGIC
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
  const { user, meta } = useAuth()
  const signOut = useSignOut()
  return (
    <aside className="sidebar">
      <Brand />
      <div className="divider-label">Faculty</div>
      <NavList items={FACULTY_NAV} onNavigate={onNavigate} />
      <div className="divider-label">Public</div>
      <NavList items={PUBLIC_NAV} onNavigate={onNavigate} />
      <div className="sidebar-foot">
        {user && (
          <div className="card card-flat" style={{ padding: 12 }}>
            <strong style={{ display: 'block', overflowWrap: 'anywhere' }}>{user.full_name}</strong>
            <span className="tiny mono muted">
              Faculty{meta?.expires_local ? ` · token expires ${meta.expires_local}` : ''}
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
      {user && <span className="badge only-desktop">{user.full_name}</span>}
      <ThemeToggle />
    </header>
  )
}

/** Faculty layout: sidebar + topbar + content; sidebar → drawer + bottom bar on small screens. */
export function AppShell({ children }) {
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  useEffect(() => setOpen(false), [loc.pathname])
  const current = FACULTY_NAV.find((n) => (n.end ? loc.pathname === n.to : loc.pathname.startsWith(n.to)))
  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={current ? `Faculty / ${current.label}` : 'Faculty'} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          {children}
        </main>
      </div>
      <nav className="bottombar" aria-label="Quick navigation">
        {FACULTY_NAV.map(({ to, short, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end}>
            <Icon size={20} aria-hidden="true" />
            {short}
          </NavLink>
        ))}
      </nav>
      <Drawer open={open} onClose={() => setOpen(false)} title="Menu" side="left">
        <div className="stack">
          <NavList items={[...FACULTY_NAV, ...PUBLIC_NAV]} onNavigate={() => setOpen(false)} />
        </div>
      </Drawer>
    </div>
  )
}

/** Public / student layout: topbar with nav + content. */
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
        <IconButton icon={Menu} label="Open navigation" className="only-mobile" onClick={() => setOpen(true)} />
        <Brand />
        <span className="topbar-spacer" />
        <nav className="public-nav" aria-label="Main">
          {PUBLIC_NAV.map((n) => (
            <NavLink key={n.to} to={n.to}>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <ThemeToggle />
        {user ? (
          user.role === 'faculty' ? (
            <Button variant="primary" size="sm" to="/app" icon={LayoutDashboard} className="only-desktop">
              Dashboard
            </Button>
          ) : (
            <Button size="sm" icon={LogOut} onClick={signOut} className="only-desktop">
              Sign out {user.roll_number}
            </Button>
          )
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
          <NavList items={[{ to: '/', label: 'Home', icon: ScanFace, end: true }, ...PUBLIC_NAV]} onNavigate={() => setOpen(false)} />
          {user ? (
            <>
              {user.role === 'faculty' && (
                <Button variant="primary" to="/app" icon={LayoutDashboard} block>
                  Faculty dashboard
                </Button>
              )}
              <Button icon={LogOut} block onClick={signOut}>
                Sign out {user.roll_number || ''}
              </Button>
            </>
          ) : (
            <>
              <Button variant="primary" to="/login" icon={LogIn} block>
                Sign in
              </Button>
              <Button to="/register" block>
                Register
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
