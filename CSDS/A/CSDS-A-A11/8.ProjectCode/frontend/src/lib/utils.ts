import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Custom easing curves shared by GSAP + Framer Motion so motion feels consistent. */
export const EASE_EXPO: [number, number, number, number] = [0.16, 1, 0.3, 1]
export const EASE_SWIFT: [number, number, number, number] = [0.32, 0.72, 0, 1]
export const GSAP_EXPO = 'cubic-bezier(0.16, 1, 0.3, 1)'

export function formatPrice(value: number | undefined | null, currency = 'USD') {
  if (value === undefined || value === null || Number.isNaN(value)) return '—'
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      maximumFractionDigits: value % 1 === 0 ? 0 : 2,
    }).format(value)
  } catch {
    return `$${value.toFixed(2)}`
  }
}

export function formatPercent(value: number | undefined | null, digits = 1) {
  if (value === undefined || value === null || Number.isNaN(value)) return '—'
  const pct = Math.abs(value) <= 1 ? value * 100 : value
  return `${pct.toFixed(digits)}%`
}

export function formatCompact(value: number | undefined | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(
    value,
  )
}

export function formatSigned(value: number, digits = 1) {
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(digits)}%`
}

export function relativeTime(iso?: string) {
  if (!iso) return ''
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return ''
  const diff = Date.now() - then
  const mins = Math.round(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.round(hrs / 24)
  if (days < 30) return `${days}d ago`
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

/** Deterministic 0..1 hash from any seed — used for generated product art. */
export function seedToUnit(seed: string | number | undefined, salt = 0): number {
  const str = `${seed ?? 'nuvara'}:${salt}`
  let h = 2166136261
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return ((h >>> 0) % 100000) / 100000
}

/** Stable pair of hues for a product's generated artwork. */
export function artGradient(seed: string | number | undefined) {
  const a = Math.round(seedToUnit(seed, 1) * 360)
  const b = (a + 40 + Math.round(seedToUnit(seed, 2) * 90)) % 360
  const angle = Math.round(seedToUnit(seed, 3) * 180)
  return {
    hueA: a,
    hueB: b,
    angle,
    css: `linear-gradient(${angle}deg, hsl(${a} 42% 26%) 0%, hsl(${b} 38% 14%) 58%, hsl(${a} 30% 9%) 100%)`,
  }
}

export function titleCase(input: string) {
  return input
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map((w) => w[0]?.toUpperCase() + w.slice(1))
    .join(' ')
}

export function normalizeWeights(w: Record<string, number>): Record<string, number> {
  const total = Object.values(w).reduce((a, b) => a + b, 0)
  if (total <= 0) {
    const even = 1 / Object.keys(w).length
    return Object.fromEntries(Object.keys(w).map((k) => [k, even]))
  }
  return Object.fromEntries(Object.entries(w).map(([k, v]) => [k, v / total]))
}
