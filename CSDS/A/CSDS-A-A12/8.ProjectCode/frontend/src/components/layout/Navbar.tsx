import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Logo } from '../ui/Logo'
import { Button } from '../ui/Button'
import { ArrowUpRight } from 'lucide-react'

const links = [
  { to: '/', label: 'Overview' },
  { to: '/app', label: 'Workspace' },
  { to: '/history', label: 'History' },
  { to: '/insights', label: 'Insights' },
]

export function Navbar() {
  const location = useLocation()

  return (
    <motion.header
      initial={{ y: -30, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className="fixed top-0 inset-x-0 z-50 px-4 pt-4"
    >
      <div className="mx-auto max-w-6xl glass rounded-full px-5 py-2.5 flex items-center justify-between">
        <Link to="/">
          <Logo />
        </Link>
        <nav className="hidden md:flex items-center gap-1">
          {links.map((link) => {
            const active = location.pathname === link.to
            return (
              <Link
                key={link.to}
                to={link.to}
                className={`relative px-4 py-2 text-sm font-medium rounded-full transition-colors ${
                  active ? 'text-[var(--color-text)]' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
                }`}
              >
                {active && (
                  <motion.span
                    layoutId="nav-pill"
                    className="absolute inset-0 rounded-full bg-emerald-500/12 border border-emerald-500/25"
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
                <span className="relative">{link.label}</span>
              </Link>
            )
          })}
        </nav>
        <Link to="/app">
          <Button size="sm" icon={<ArrowUpRight size={15} />}>
            Launch
          </Button>
        </Link>
      </div>
    </motion.header>
  )
}
