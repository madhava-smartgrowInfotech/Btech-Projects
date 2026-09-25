import { Link } from 'react-router-dom'
import { ArrowUpRight } from 'lucide-react'
import { Logo } from './Logo'
import { Marquee } from '@/components/bits/Marquee'

const COLUMNS = [
  {
    title: 'Catalog',
    links: [
      { label: 'All products', to: '/shop' },
      { label: 'Lighting', to: '/shop/lighting' },
      { label: 'Audio', to: '/shop/audio' },
      { label: 'Workspace', to: '/shop/workspace' },
    ],
  },
  {
    title: 'Company',
    links: [
      { label: 'Our materials', to: '/shop' },
      { label: 'Design principles', to: '/shop' },
      { label: 'Stores', to: '/shop' },
      { label: 'Careers', to: '/shop' },
    ],
  },
  {
    title: 'Support',
    links: [
      { label: 'Shipping & returns', to: '/cart' },
      { label: 'Warranty', to: '/cart' },
      { label: 'Care guide', to: '/cart' },
      { label: 'Contact', to: '/cart' },
    ],
  },
]

const MARQUEE_WORDS = [
  'Designed in Copenhagen',
  'Assembled in Portugal',
  'Carbon-neutral delivery',
  'Ten-year warranty',
  'Repairable by design',
]

export function Footer() {
  return (
    <footer className="relative mt-28 border-t border-white/[0.07] bg-ink-950">
      <div className="border-b border-white/[0.05] py-6">
        <Marquee speed={44}>
          {MARQUEE_WORDS.map((word) => (
            <span
              key={word}
              className="flex items-center gap-12 text-[13px] uppercase tracking-[0.26em] text-ink-600"
            >
              {word}
              <span className="h-1 w-1 rounded-full bg-amber-400/60" />
            </span>
          ))}
        </Marquee>
      </div>

      <div className="container grid gap-12 py-16 md:grid-cols-[1.4fr_2fr]">
        <div>
          <Logo />
          <p className="mt-5 max-w-sm text-[14px] leading-relaxed text-ink-400">
            Nuvara makes a small, considered range of objects for the places you spend the most
            time — and a recommendation layer that learns what you actually reach for.
          </p>
          <Link
            to="/intelligence"
            className="mt-6 inline-flex items-center gap-1.5 text-[13px] text-amber-300 transition-colors hover:text-amber-200"
          >
            Explore Nuvara Intelligence
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-2 gap-8 sm:grid-cols-3">
          {COLUMNS.map((column) => (
            <div key={column.title}>
              <p className="eyebrow mb-4">{column.title}</p>
              <ul className="space-y-2.5">
                {column.links.map((link) => (
                  <li key={link.label}>
                    <Link
                      to={link.to}
                      className="text-[13.5px] text-ink-400 transition-colors duration-300 ease-expo hover:text-ink-100"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      <div className="container flex flex-col gap-3 border-t border-white/[0.05] py-6 text-[12px] text-ink-600 sm:flex-row sm:items-center sm:justify-between">
        <p>© {new Date().getFullYear()} Nuvara. All rights reserved.</p>
        <p className="flex items-center gap-4">
          <span>Privacy</span>
          <span>Terms</span>
          <span>Accessibility</span>
        </p>
      </div>
    </footer>
  )
}
