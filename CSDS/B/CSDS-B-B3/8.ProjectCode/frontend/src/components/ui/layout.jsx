import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useOutlet } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import {
  Code2,
  FlaskConical,
  GraduationCap,
  Home,
  LayoutDashboard,
  BookOpen,
  LogOut,
  Menu,
  Mic,
  Moon,
  Network,
  Store,
  Sun,
  Target,
  TrendingUp,
  User,
  Users,
  ShieldCheck,
} from 'lucide-react'
import { useTheme } from '../../lib/theme'
import { useAuth } from '../../lib/auth'
import { PageTransition } from '../motion'
import { Button, IconButton } from './controls'
import { Badge } from './display'
import { Drawer, Tooltip } from './feedback'
import { Breadcrumbs } from './navigation'

const RESEARCH = { to: '/app/research', label: 'Research & Innovation', icon: FlaskConical }
const MARKET = { to: '/app/marketplace', label: 'Marketplace', icon: Store }
const PROFILE = { to: '/app/profile', label: 'Profile', icon: User }

// Same role-based navigation the Streamlit app had (STUDENT_NAV / MENTOR_NAV / ADMIN_NAV)
export const NAV_BY_ROLE = {
  student: [
    { to: '/app/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/app/learning', label: 'Learning', icon: BookOpen },
    { to: '/app/graph', label: 'Knowledge Graph', icon: Network },
    { to: '/app/career', label: 'Career AI', icon: Target },
    MARKET,
    { to: '/app/mentors', label: 'Mentors', icon: Users },
    { to: '/app/interview', label: 'Mock Interview', icon: Mic },
    { to: '/app/coding', label: 'Coding Practice', icon: Code2 },
    { to: '/app/progress', label: 'Progress', icon: TrendingUp },
    RESEARCH,
    PROFILE,
  ],
  mentor: [{ to: '/app/mentor-panel', label: 'Mentor Panel', icon: GraduationCap }, MARKET, RESEARCH, PROFILE],
  admin: [{ to: '/app/admin', label: 'Admin Panel', icon: ShieldCheck }, RESEARCH],
}

export const homeFor = (role) => NAV_BY_ROLE[role]?.[0]?.to || '/login'

export function Container({ children, className = '' }) {
  return <div className={`container ${className}`}>{children}</div>
}

export function BrandMark({ size = 18 }) {
  return (
    <span className="brand-mark" aria-hidden="true">
      <GraduationCap size={size} strokeWidth={2.2} />
    </span>
  )
}

export function Sidebar({ onNavigate, pillId = 'nav-pill' }) {
  const { user, logout } = useAuth()
  const nav = NAV_BY_ROLE[user?.role] || []
  return (
    <aside className="sidebar" aria-label="Main">
      <Link to="/" className="brand" onClick={onNavigate}>
        <BrandMark />
        <span>
          SkillVerse
          <small>Learn. Earn. Connect. Grow.</small>
        </span>
      </Link>
      <nav aria-label="App sections" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div className="nav-label">{user?.role ? `${user.role[0].toUpperCase()}${user.role.slice(1)} workspace` : 'Workspace'}</div>
        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`} onClick={onNavigate}>
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
        <div style={{ fontWeight: 600 }} className="break">
          {user?.name}
        </div>
        <div className="faint break" style={{ marginBottom: 10 }}>
          {user?.email}
        </div>
        <Button size="sm" icon={LogOut} onClick={logout} style={{ width: '100%' }}>
          Log out
        </Button>
      </div>
    </aside>
  )
}

export function Topbar({ title, onMenu }) {
  const { theme, toggle } = useTheme()
  const { user } = useAuth()
  const label = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
  return (
    <header className="topbar">
      <IconButton icon={Menu} label="Open navigation" className="menu-btn" onClick={onMenu} />
      <div className="topbar-title">{title}</div>
      <div className="topbar-spacer" />
      {user && (
        <span className="hide-sm">
          <Badge tone="safe" dot>
            {user.role[0].toUpperCase() + user.role.slice(1)}
          </Badge>
        </span>
      )}
      <Tooltip label={label} placement="bottom">
        <IconButton icon={theme === 'dark' ? Sun : Moon} label={label} onClick={toggle} />
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
  const { user } = useAuth()
  const current = (NAV_BY_ROLE[user?.role] || []).find((n) => loc.pathname.startsWith(n.to))

  useEffect(() => {
    document.title = `${current ? current.label : 'App'} · SkillVerse`
    setOpen(false)
  }, [loc.pathname, current])

  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={current?.label || 'SkillVerse'} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          <AnimatePresence mode="wait" initial={false}>
            <PageTransition key={loc.pathname}>
                <Container>{outlet}</Container>
              </PageTransition>
          </AnimatePresence>
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
