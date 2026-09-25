import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Menu, Search, ShoppingBag, Sparkles, X } from 'lucide-react'
import { Logo } from './Logo'
import { PersonaSwitcher } from './PersonaSwitcher'
import { Input } from '@/components/ui/input'
import { cartCount, useCart } from '@/store/cart'
import { useTracking } from '@/hooks/useTracking'
import { EASE_EXPO, cn } from '@/lib/utils'

const NAV = [
  { to: '/shop', label: 'Shop' },
  { to: '/shop/lighting', label: 'Lighting' },
  { to: '/shop/audio', label: 'Audio' },
  { to: '/shop/workspace', label: 'Workspace' },
]

export function Header() {
  const [scrolled, setScrolled] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [query, setQuery] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()
  const location = useLocation()
  const lines = useCart((s) => s.lines)
  const { track } = useTracking()
  const count = cartCount(lines)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    setMobileOpen(false)
    setSearchOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (searchOpen) requestAnimationFrame(() => inputRef.current?.focus())
  }, [searchOpen])

  const submitSearch = (event: FormEvent) => {
    event.preventDefault()
    const q = query.trim()
    if (!q) return
    track({ type: 'search', query: q })
    navigate(`/shop?q=${encodeURIComponent(q)}`)
    setSearchOpen(false)
  }

  return (
    <header
      className={cn(
        'fixed inset-x-0 top-0 z-50 transition-[background-color,border-color,backdrop-filter] duration-500 ease-expo',
        scrolled
          ? 'border-b border-white/[0.07] bg-ink-950/80 backdrop-blur-xl'
          : 'border-b border-transparent bg-transparent',
      )}
    >
      <div className="container flex h-[68px] items-center gap-4">
        <Link to="/" className="shrink-0" aria-label="Nuvara home">
          <Logo />
        </Link>

        <nav className="ml-6 hidden items-center gap-1 lg:flex">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/shop'}
              className={({ isActive }) =>
                cn(
                  'relative rounded-full px-3.5 py-2 text-[13.5px] transition-colors duration-300 ease-expo',
                  isActive ? 'text-ink-100' : 'text-ink-400 hover:text-ink-100',
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => setSearchOpen((v) => !v)}
            className="grid h-10 w-10 place-items-center rounded-full border border-white/[0.08] bg-white/[0.02] text-ink-300 transition-colors duration-300 ease-expo hover:border-white/20 hover:text-ink-100"
            aria-label="Search the catalog"
          >
            <Search className="h-4 w-4" />
          </button>

          <div className="hidden sm:block">
            <PersonaSwitcher />
          </div>

          <NavLink
            to="/intelligence"
            className={({ isActive }) =>
              cn(
                'hidden h-10 items-center gap-2 rounded-full border px-3.5 text-[12.5px] font-medium transition-all duration-300 ease-expo md:inline-flex',
                isActive
                  ? 'border-amber-400/40 bg-amber-400/10 text-amber-200'
                  : 'border-white/[0.09] bg-white/[0.02] text-ink-300 hover:border-amber-400/30 hover:text-amber-200',
              )
            }
          >
            <Sparkles className="h-3.5 w-3.5" />
            Intelligence
          </NavLink>

          <Link
            to="/cart"
            className="relative grid h-10 w-10 place-items-center rounded-full border border-white/[0.08] bg-white/[0.02] text-ink-300 transition-colors duration-300 ease-expo hover:border-white/20 hover:text-ink-100"
            aria-label={`Bag, ${count} item${count === 1 ? '' : 's'}`}
          >
            <ShoppingBag className="h-4 w-4" />
            <AnimatePresence>
              {count > 0 && (
                <motion.span
                  key={count}
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.5, opacity: 0 }}
                  transition={{ duration: 0.3, ease: EASE_EXPO }}
                  className="absolute -right-0.5 -top-0.5 grid h-[18px] min-w-[18px] place-items-center rounded-full bg-amber-400 px-1 text-[10px] font-semibold text-ink-950"
                >
                  {count}
                </motion.span>
              )}
            </AnimatePresence>
          </Link>

          <button
            onClick={() => setMobileOpen((v) => !v)}
            className="grid h-10 w-10 place-items-center rounded-full border border-white/[0.08] bg-white/[0.02] text-ink-300 lg:hidden"
            aria-label="Menu"
          >
            {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {searchOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.45, ease: EASE_EXPO }}
            className="overflow-hidden border-t border-white/[0.06] bg-ink-950/90 backdrop-blur-xl"
          >
            <form onSubmit={submitSearch} className="container flex items-center gap-3 py-4">
              <Search className="h-4 w-4 shrink-0 text-ink-500" />
              <Input
                ref={inputRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search lighting, audio, workspace…"
                className="h-11 border-transparent bg-transparent px-0 text-[15px] focus:border-transparent"
              />
              <button
                type="button"
                onClick={() => setSearchOpen(false)}
                className="rounded-full p-2 text-ink-500 hover:text-ink-200"
                aria-label="Close search"
              >
                <X className="h-4 w-4" />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.45, ease: EASE_EXPO }}
            className="overflow-hidden border-t border-white/[0.06] bg-ink-950/95 backdrop-blur-xl lg:hidden"
          >
            <div className="container flex flex-col gap-1 py-4">
              {NAV.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className="rounded-xl px-3 py-3 text-[15px] text-ink-200 hover:bg-white/[0.05]"
                >
                  {item.label}
                </Link>
              ))}
              <Link
                to="/intelligence"
                className="flex items-center gap-2 rounded-xl px-3 py-3 text-[15px] text-amber-200 hover:bg-white/[0.05]"
              >
                <Sparkles className="h-4 w-4" />
                Nuvara Intelligence
              </Link>
              <div className="px-3 pt-3 sm:hidden">
                <PersonaSwitcher />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
