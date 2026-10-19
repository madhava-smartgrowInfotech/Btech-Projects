import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { AudioLines, BarChart3, BookOpen, Home, Library, Menu, Moon, PenLine, Sun } from 'lucide-react'
import { useTheme } from '../../lib/theme'
import { useMeta } from '../../lib/meta'
import { Button, IconButton } from './Button'
import { Drawer } from './Feedback'

export const APP_NAV = [
  { to: '/', label: 'Home', short: 'Home', icon: Home, end: true },
  { to: '/studio', label: 'Studio', short: 'Studio', icon: PenLine },
  { to: '/stories', label: 'History', short: 'History', icon: Library },
  { to: '/evaluation', label: 'Evaluation', short: 'Eval', icon: BarChart3 },
]
const PUBLIC_NAV = [
  { to: '/#how', label: 'How it works', icon: BookOpen, hash: true },
  { to: '/stories', label: 'History', icon: Library },
  { to: '/evaluation', label: 'Evaluation', icon: BarChart3 },
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
    <Link to="/" className="brand" aria-label="StoryVox home">
      <span className="brand-mark" aria-hidden="true">
        <AudioLines size={20} strokeWidth={2.75} />
      </span>
      <span>
        STORY
        <br />
        VOX
      </span>
    </Link>
  )
}

export function ThemeToggle() {
  const { theme, toggle } = useTheme()
  return <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
}

/** Live API status from /api/health: online + compute device, or a clear offline notice. */
export function ApiStatus() {
  const { loading, error, health } = useMeta()
  if (loading) return <span className="badge">Checking API…</span>
  if (error || !health) return <span className="badge badge-blocked">API offline</span>
  return (
    <span className="badge badge-live" title="Backend is reachable">
      <span className="badge-dot" aria-hidden="true" />
      API online · {health.cuda ? 'GPU' : 'CPU'}
    </span>
  )
}

function NavList({ items, onNavigate }) {
  return (
    <nav className="sidebar-nav" aria-label="Main">
      {items.map(({ to, label, icon: Icon, end, hash }) =>
        hash ? (
          <a key={to} href={to} className="nav-link" onClick={onNavigate}>
            <Icon size={20} aria-hidden="true" />
            {label}
          </a>
        ) : (
          <NavLink key={to} to={to} end={end} className="nav-link" onClick={onNavigate}>
            <Icon size={20} aria-hidden="true" />
            {label}
          </NavLink>
        ),
      )}
    </nav>
  )
}

export function Sidebar({ onNavigate }) {
  const { meta } = useMeta()
  return (
    <aside className="sidebar">
      <Brand />
      <div className="divider-label">Workspace</div>
      <NavList items={APP_NAV} onNavigate={onNavigate} />
      <div className="sidebar-foot">
        <div className="card card-flat" style={{ padding: 12 }}>
          <strong style={{ display: 'block' }}>Local-first</strong>
          <span className="tiny muted">Stories and audio stay on this computer. No uploads.</span>
          {meta?.story_model && <span className="tiny mono muted" style={{ display: 'block', marginTop: 8, overflowWrap: 'anywhere' }}>{meta.story_model}</span>}
        </div>
      </div>
    </aside>
  )
}

export function Topbar({ title, onMenu }) {
  return (
    <header className="topbar">
      {onMenu && <IconButton icon={Menu} label="Open navigation" className="only-mobile" onClick={onMenu} />}
      <span className="only-mobile">
        <Brand />
      </span>
      {title && <span className="topbar-title only-desktop">{title}</span>}
      <span className="topbar-spacer" />
      <span className="only-desktop">
        <ApiStatus />
      </span>
      <ThemeToggle />
    </header>
  )
}

/** App layout: sidebar + topbar + content; sidebar becomes a drawer plus a bottom bar on small screens. */
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
        <Topbar title={current ? `StoryVox / ${current.label}` : 'StoryVox'} onMenu={() => setOpen(true)} />
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
          <ApiStatus />
        </div>
      </Drawer>
    </div>
  )
}

/** Landing layout: topbar with nav + content. */
export function PublicShell({ children }) {
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
          {PUBLIC_NAV.map((n) =>
            n.hash ? (
              <a key={n.to} href={n.to}>
                {n.label}
              </a>
            ) : (
              <NavLink key={n.to} to={n.to}>
                {n.label}
              </NavLink>
            ),
          )}
        </nav>
        <ThemeToggle />
        <Button variant="primary" size="sm" to="/studio" icon={PenLine} className="only-desktop">
          Open studio
        </Button>
      </header>
      <main id="main" tabIndex={-1}>
        {children}
      </main>
      <Drawer open={open} onClose={() => setOpen(false)} title="Menu" side="left">
        <div className="stack">
          <NavList items={[{ to: '/', label: 'Home', icon: Home, end: true }, ...PUBLIC_NAV]} onNavigate={() => setOpen(false)} />
          <Button variant="primary" to="/studio" icon={PenLine} block>
            Open studio
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
