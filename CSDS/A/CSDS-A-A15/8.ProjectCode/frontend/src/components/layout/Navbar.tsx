import { motion, useScroll, useTransform } from 'framer-motion'
import { ScanEye } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'

export function Navbar() {
  const { scrollY } = useScroll()
  const bg = useTransform(scrollY, [0, 80], ['rgba(5,7,12,0)', 'rgba(5,7,12,0.75)'])
  const borderOpacity = useTransform(scrollY, [0, 80], [0, 1])
  const { user } = useAuth()

  return (
    <motion.header
      style={{ backgroundColor: bg, backdropFilter: 'blur(12px)' }}
      className="fixed top-0 inset-x-0 z-50"
    >
      <motion.div
        style={{ opacity: borderOpacity }}
        className="absolute bottom-0 inset-x-0 h-px bg-white/10"
      />
      <div className="mx-auto max-w-7xl px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-display font-semibold text-white">
          <ScanEye className="h-5 w-5 text-cyan-400" />
          VisionForge <span className="text-gradient">AI</span>
        </Link>
        <nav className="hidden md:flex items-center gap-8 text-sm text-slate-300">
          <a href="#platform" className="hover:text-white transition">Platform</a>
          <a href="#how-it-works" className="hover:text-white transition">How it works</a>
          <a href="#performance" className="hover:text-white transition">Performance</a>
        </nav>
        <div className="flex items-center gap-3">
          {user ? (
            <Link
              to="/app/dashboard"
              className="rounded-xl bg-gradient-to-r from-cyan-400 to-violet-500 px-5 py-2.5 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40 transition-shadow"
            >
              Open Dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="text-sm text-slate-300 hover:text-white transition hidden sm:block">
                Sign in
              </Link>
              <Link
                to="/signup"
                className="rounded-xl bg-gradient-to-r from-cyan-400 to-violet-500 px-5 py-2.5 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40 transition-shadow"
              >
                Get Started
              </Link>
            </>
          )}
        </div>
      </div>
    </motion.header>
  )
}
