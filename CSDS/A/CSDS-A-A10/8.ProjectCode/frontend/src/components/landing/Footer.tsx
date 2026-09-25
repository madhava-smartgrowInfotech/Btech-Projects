import { Activity } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/Button'

export function Footer() {
  return (
    <footer className="relative border-t border-white/8 py-16">
      <div className="mx-auto max-w-7xl px-6">
        <div className="flex flex-col items-center justify-between gap-8 rounded-3xl border border-white/8 bg-gradient-to-br from-brand-600/20 via-ink-900 to-ink-900 p-10 text-center sm:p-14">
          <h2 className="font-display text-2xl font-bold text-white sm:text-3xl text-balance">
            Ready to see MedFlow running your floor?
          </h2>
          <p className="max-w-md text-sm text-ink-400">
            Sign in with any staff role to explore the live console, or open the public waiting-room
            board.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link to="/login">
              <Button size="lg">Open Staff Console</Button>
            </Link>
            <Link to="/board">
              <Button size="lg" variant="outline">
                View Waiting Board
              </Button>
            </Link>
          </div>
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 text-sm text-ink-500 sm:flex-row">
          <div className="flex items-center gap-2">
            <Activity size={15} />
            <span className="font-display font-semibold text-ink-300">MedFlow</span>
          </div>
          <p>Hospital Patient Flow Intelligence Platform</p>
        </div>
      </div>
    </footer>
  )
}
