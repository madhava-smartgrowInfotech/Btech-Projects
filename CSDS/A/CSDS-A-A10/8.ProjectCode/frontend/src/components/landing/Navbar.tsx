import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, Menu, X } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/Button'

const LINKS = [
  { label: 'Platform', href: '#platform' },
  { label: 'Workflow', href: '#workflow' },
  { label: 'Intelligence', href: '#intelligence' },
  { label: 'Results', href: '#results' },
]

export function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <motion.header
      initial={{ y: -80 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        scrolled ? 'border-b border-white/8 bg-ink-950/80 backdrop-blur-xl' : 'bg-transparent'
      }`}
    >
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <a href="#top" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-400 to-vital-500 shadow-lg shadow-brand-500/30">
            <Activity size={17} className="text-white" strokeWidth={2.5} />
          </div>
          <span className="font-display text-base font-bold tracking-tight text-white">
            Med<span className="text-brand-400">Flow</span>
          </span>
        </a>

        <div className="hidden items-center gap-8 md:flex">
          {LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-ink-300 transition-colors hover:text-white"
            >
              {link.label}
            </a>
          ))}
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <Link to="/board" className="text-sm font-medium text-ink-300 hover:text-white">
            Waiting Board
          </Link>
          <Link to="/login">
            <Button size="sm">Staff Sign In</Button>
          </Link>
        </div>

        <button className="text-ink-200 md:hidden" onClick={() => setOpen(!open)}>
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </nav>

      {open && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          className="border-t border-white/8 bg-ink-950/95 px-6 py-4 md:hidden"
        >
          <div className="flex flex-col gap-3">
            {LINKS.map((link) => (
              <a key={link.href} href={link.href} className="text-sm text-ink-300" onClick={() => setOpen(false)}>
                {link.label}
              </a>
            ))}
            <Link to="/login">
              <Button size="sm" className="mt-2 w-full">
                Staff Sign In
              </Button>
            </Link>
          </div>
        </motion.div>
      )}
    </motion.header>
  )
}
