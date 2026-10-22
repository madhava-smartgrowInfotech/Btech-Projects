import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import {
  Activity,
  BarChart3,
  BookOpen,
  Compass,
  LayoutDashboard,
  LogIn,
  LogOut,
  Menu,
  Moon,
  Route,
  Sparkles,
  Sun,
  UserRound,
  Lightbulb,
} from 'lucide-react'
import { useAuth } from '../../lib/auth'
import { useTheme } from '../../lib/theme'
import { Button, IconButton } from './Button'
import { Drawer } from './Feedback'
import { useToast } from './Toast'

export const LEARNER_NAV = [
  { to: '/app', label: 'Dashboard', short: 'Home', icon: LayoutDashboard, end: true },
  { to: '/app/recommendations', label: 'Recommendations', short: 'For you', icon: Sparkles },
  { to: '/app/path', label: 'Learning path', short: 'Path', icon: Route },
  { to: '/app/insights', label: 'Insights', short: 'Insights', icon: Lightbulb },
  { to: '/app/activity', label: 'Activity', icon: Activity },
  { to: '/app/profile', label: 'My profile', icon: UserRound },
]
const BOTTOM_NAV = LEARNER_NAV.slice(0, 4)
const EXPLORE_NAV = [
  { to: '/courses', label: 'Course catalog', icon: BookOpen },
  { to: '/analytics', label: 'Model analytics', icon: BarChart3 },
]
const PUBLIC_NAV = [
  { to: '/courses', label: 'Courses' },
  { to: '/analytics', label: 'Analytics' },
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
    <Link to="/" className="brand" aria-label="LearnPathIQ home">
      <span className="brand-mark" aria-hidden="true">
        LP
      </span>
      <span>
        LEARN
        <br />
        PATH IQ
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
    try {
      await logout()
      toast.info('Signed out.')
    } catch (e) {
      toast.error(`Sign-out failed: ${e.message}`)
    }
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
      <div className="divider-label">Learner</div>
      <NavList items={LEARNER_NAV} onNavigate={onNavigate} />
      <div className="divider-label">Explore</div>
      <NavList items={EXPLORE_NAV} onNavigate={onNavigate} />
      <div className="sidebar-foot">
        {user && (
          <div className="card card-flat" style={{ padding: 12 }}>
            <strong style={{ display: 'block', overflowWrap: 'anywhere' }}>{user.name}</strong>
            <span className="tiny mono muted" style={{ overflowWrap: 'anywhere' }}>
              {user.email}
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

/** Learner layout: sidebar + topbar + content; sidebar becomes a drawer + bottom bar on small screens. */
export function AppShell({ children }) {
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  const signOut = useSignOut()
  useEffect(() => setOpen(false), [loc.pathname])
  const all = [...LEARNER_NAV, ...EXPLORE_NAV]
  const current = all.find((n) => (n.end ? loc.pathname === n.to : loc.pathname.startsWith(n.to)))
  const title = current ? current.label : loc.pathname.startsWith('/courses') ? 'Course catalog' : 'LearnPathIQ'
  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={title} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          {children}
        </main>
      </div>
      <nav className="bottombar" aria-label="Quick navigation">
        {BOTTOM_NAV.map(({ to, short, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end}>
            <Icon size={20} aria-hidden="true" />
            {short}
          </NavLink>
        ))}
      </nav>
      <Drawer open={open} onClose={() => setOpen(false)} title="Menu" side="left">
        <div className="stack">
          <NavList items={all} onNavigate={() => setOpen(false)} />
          <Button icon={LogOut} block onClick={signOut}>
            Sign out
          </Button>
        </div>
      </Drawer>
    </div>
  )
}

function Footer() {
  return (
    <footer className="footer">
      <Container>
        <div className="footer-grid">
          <div className="stack" style={{ '--gap': '10px' }}>
            <span className="display-sm">LEARNPATHIQ</span>
            <p className="small">Personalized course recommendations. Every suggestion ships with its reasons.</p>
          </div>
          <div>
            <h4>Explore</h4>
            <ul>
              <li>
                <Link to="/courses">Course catalog</Link>
              </li>
              <li>
                <Link to="/analytics">Model analytics</Link>
              </li>
            </ul>
          </div>
          <div>
            <h4>Honest by design</h4>
            <p className="small">
              Action scores are estimated benefits from observed patterns, not proven causal effects. Offline estimates only; no live A/B
              testing.
            </p>
          </div>
        </div>
      </Container>
    </footer>
  )
}

/** Public layout: topbar with nav + content + footer. */
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
          <Button variant="primary" size="sm" to="/app" icon={LayoutDashboard} className="only-desktop">
            Dashboard
          </Button>
        ) : (
          <>
            <Button size="sm" to="/login" icon={LogIn} className="only-desktop">
              Sign in
            </Button>
            <Button variant="primary" size="sm" to="/register" icon={Compass} className="only-desktop">
              Get started
            </Button>
          </>
        )}
      </header>
      <main id="main" tabIndex={-1}>
        {children}
      </main>
      <Footer />
      <Drawer open={open} onClose={() => setOpen(false)} title="Menu" side="left">
        <div className="stack">
          <NavList
            items={[{ to: '/', label: 'Home', icon: Compass, end: true }, ...EXPLORE_NAV]}
            onNavigate={() => setOpen(false)}
          />
          {user ? (
            <>
              <Button variant="primary" to="/app" icon={LayoutDashboard} block>
                My dashboard
              </Button>
              <Button icon={LogOut} block onClick={signOut}>
                Sign out
              </Button>
            </>
          ) : (
            <>
              <Button variant="primary" to="/register" block>
                Get started
              </Button>
              <Button to="/login" icon={LogIn} block>
                Sign in
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
