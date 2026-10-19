import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate, useOutlet } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import {
  BarChart3,
  CalendarClock,
  CarFront,
  Gauge,
  Home,
  ListChecks,
  LogOut,
  MapPin,
  Menu,
  Moon,
  ParkingSquare,
  Search,
  Sun,
  Users,
  Wallet,
} from 'lucide-react'
import { useTheme } from '../../lib/theme'
import { useAuth } from '../../lib/auth'
import { money } from '../../lib/format'
import { PageTransition } from '../motion'
import { IconButton } from './controls'
import { Badge } from './display'
import { Drawer, Tooltip } from './feedback'
import { Breadcrumbs } from './navigation'

export const NAV = [
  { to: '/app/find', label: 'Find parking', icon: Search, group: 'driver' },
  { to: '/app/bookings', label: 'My bookings', icon: CalendarClock, group: 'driver' },
  { to: '/app/trust', label: 'Trust score', icon: Gauge, group: 'driver' },
  { to: '/app/admin', label: 'Overview', icon: Home, group: 'admin', end: true },
  { to: '/app/admin/locations', label: 'Locations', icon: MapPin, group: 'admin' },
  { to: '/app/admin/insights', label: 'Strategy insights', icon: BarChart3, group: 'admin' },
  { to: '/app/admin/bookings', label: 'All bookings', icon: ListChecks, group: 'admin' },
  { to: '/app/admin/users', label: 'Users', icon: Users, group: 'admin' },
]

const matchNav = (path) => NAV.find((n) => (n.end ? path === n.to : path === n.to || path.startsWith(`${n.to}/`)))

export function Container({ children, className = '' }) {
  return <div className={`container ${className}`}>{children}</div>
}

export function BrandMark({ size = 18 }) {
  return (
    <span className="brand-mark" aria-hidden="true">
      <ParkingSquare size={size} strokeWidth={2.4} />
    </span>
  )
}

export function Sidebar({ onNavigate, pillId = 'nav-pill' }) {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const link = ({ to, label, icon: Icon, end }) => (
    <NavLink key={to} to={to} end={end} className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`} onClick={onNavigate}>
      {({ isActive }) => (
        <>
          {isActive && <motion.span layoutId={pillId} className="nav-pill" transition={{ type: 'spring', stiffness: 400, damping: 34 }} />}
          <Icon size={18} aria-hidden="true" />
          <span>{label}</span>
        </>
      )}
    </NavLink>
  )
  return (
    <aside className="sidebar" aria-label="Main">
      <Link to="/" className="brand" onClick={onNavigate}>
        <BrandMark />
        <span>
          ParkSure
          <small>Smart parking reservations</small>
        </span>
      </Link>
      <nav aria-label="App sections" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div className="nav-label">Driver</div>
        {NAV.filter((n) => n.group === 'driver').map(link)}
        {isAdmin && (
          <>
            <div className="nav-label">Admin</div>
            {NAV.filter((n) => n.group === 'admin').map(link)}
          </>
        )}
        <div className="nav-label">Site</div>
        <NavLink to="/" end className="nav-link" onClick={onNavigate}>
          <CarFront size={18} aria-hidden="true" />
          <span>Landing page</span>
        </NavLink>
      </nav>
      <div className="sidebar-foot">
        <div className="faint" style={{ marginBottom: 4 }}>
          Signed in as
        </div>
        <div style={{ fontWeight: 600 }} className="break">
          {user?.name}
        </div>
        <div className="faint">{user?.role === 'admin' ? 'Administrator' : 'Driver'}</div>
      </div>
    </aside>
  )
}

export function Topbar({ title, onMenu }) {
  const { theme, toggle } = useTheme()
  const { user, logout } = useAuth()
  const nav = useNavigate()
  return (
    <header className="topbar">
      <IconButton icon={Menu} label="Open navigation" className="menu-btn" onClick={onMenu} />
      <div className="topbar-title">{title}</div>
      <div className="topbar-spacer" />
      {user && (
        <span className="hide-sm">
          <Tooltip label="Account credit is applied to your next booking" placement="bottom">
            <Badge tone={user.account_credit > 0 ? 'safe' : 'neutral'}>
              <Wallet size={13} aria-hidden="true" /> Credit {money(user.account_credit)}
            </Badge>
          </Tooltip>
        </span>
      )}
      <Tooltip label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} placement="bottom">
        <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
      </Tooltip>
      <Tooltip label="Log out" placement="bottom">
        <IconButton
          icon={LogOut}
          label="Log out"
          onClick={() => {
            logout({ home: true })
            nav('/')
          }}
        />
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
  const current = matchNav(loc.pathname)

  useEffect(() => {
    document.title = `${current ? current.label : 'App'} · ParkSure`
    setOpen(false)
  }, [loc.pathname, current])

  return (
    <div className="shell">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <Sidebar />
      <div className="shell-main">
        <Topbar title={current?.label || 'ParkSure'} onMenu={() => setOpen(true)} />
        <main id="main" className="shell-content" tabIndex={-1}>
          <AnimatePresence mode="wait" initial={false}>
            <PageTransition key={loc.pathname}>{outlet}</PageTransition>
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
