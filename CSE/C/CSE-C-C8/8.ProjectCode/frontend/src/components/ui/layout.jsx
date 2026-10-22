import { Suspense, useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useOutlet } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { BarChart3, FileSearch, History, Home, Info, LayoutDashboard, Menu, Moon, ScanSearch, Sun, Users } from 'lucide-react'
import { useTheme } from '../../lib/theme'
import { useStats } from '../../lib/stats'
import { PageTransition } from '../motion'
import { IconButton } from './controls'
import { Badge } from './display'
import { Drawer, Skeleton, Tooltip } from './feedback'
import { Breadcrumbs } from './navigation'

export const NAV = [
  { to: '/app', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/app/analyze', label: 'Analyze paper', icon: ScanSearch },
  { to: '/app/reviewers', label: 'Reviewers', icon: Users },
  { to: '/app/model', label: 'Model performance', icon: BarChart3 },
  { to: '/app/history', label: 'Analysis history', icon: History },
  { to: '/app/about', label: 'About & responsible use', icon: Info },
]

const isCurrent = (n, pathname) => (n.end ? pathname === n.to : pathname === n.to || pathname.startsWith(`${n.to}/`))

export function Container({ children, className = '' }) {
  return <div className={`container ${className}`}>{children}</div>
}

export function BrandMark({ size = 18 }) {
  return (
    <span className="brand-mark" aria-hidden="true">
      <FileSearch size={size} strokeWidth={2.4} />
    </span>
  )
}

export function Sidebar({ onNavigate, pillId = 'nav-pill' }) {
  const { health, error } = useStats()
  return (
    <aside className="sidebar" aria-label="Main">
      <Link to="/" className="brand" onClick={onNavigate}>
        <BrandMark />
        <span>
          PeerScope
          <small>Paper evaluation &amp; reviewer matching</small>
        </span>
      </Link>
      <nav aria-label="App sections" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div className="nav-label">Workspace</div>
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
        <div className="faint" style={{ marginBottom: 4 }}>
          Decision model
        </div>
        {error ? (
          <Badge tone="danger" dot>
            Backend offline
          </Badge>
        ) : health ? (
          <Badge tone={health.model_loaded ? 'safe' : 'warn'} dot>
            {health.model_loaded ? 'Trained model loaded' : 'Model not trained'}
          </Badge>
        ) : (
          <span className="faint">Checking…</span>
        )}
      </div>
    </aside>
  )
}

export function Topbar({ title, onMenu }) {
  const { theme, toggle } = useTheme()
  const { error, health } = useStats()
  return (
    <header className="topbar">
      <IconButton icon={Menu} label="Open navigation" className="menu-btn" onClick={onMenu} />
      <div className="topbar-title">{title}</div>
      <div className="topbar-spacer" />
      {error ? (
        <Badge tone="danger" dot>
          Offline
        </Badge>
      ) : (
        health && (
          <span className="hide-sm">
            <Badge tone={health.llm_status === 'loaded' ? 'safe' : 'info'} dot>
              {health.reviewer_count} reviewers · AI review {health.llm_status === 'loaded' ? 'ready' : 'on demand'}
            </Badge>
          </span>
        )
      )}
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
  const current = NAV.find((n) => isCurrent(n, loc.pathname))

  useEffect(() => {
    document.title = `${current ? current.label : 'PeerScope'} · PeerScope`
    setOpen(false)
  }, [loc.pathname, current])

  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={current?.label || 'PeerScope'} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          <AnimatePresence mode="wait" initial={false}>
            <PageTransition key={loc.pathname}>
              <Suspense
                fallback={
                  <Container>
                    <div aria-busy="true" aria-label="Loading screen">
                      <Skeleton width={240} height={32} />
                      <Skeleton height={14} width={380} style={{ marginTop: 14 }} />
                      <Skeleton height={150} style={{ marginTop: 26 }} radius="18px" />
                    </div>
                  </Container>
                }
              >
                {outlet}
              </Suspense>
            </PageTransition>
          </AnimatePresence>
          <Container>
            <p className="disclaimer-foot">
              PeerScope provides AI-assisted analysis and reviewer matching for decision support. Final editorial judgment remains with a qualified human.
            </p>
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
