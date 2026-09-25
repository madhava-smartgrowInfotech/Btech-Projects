import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPercent(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export const SEVERITY_STYLES: Record<string, { text: string; bg: string; ring: string; dot: string }> = {
  low: { text: 'text-emerald-400', bg: 'bg-emerald-400/10', ring: 'ring-emerald-400/30', dot: 'bg-emerald-400' },
  medium: { text: 'text-amber-400', bg: 'bg-amber-400/10', ring: 'ring-amber-400/30', dot: 'bg-amber-400' },
  high: { text: 'text-rose-400', bg: 'bg-rose-400/10', ring: 'ring-rose-400/30', dot: 'bg-rose-400' },
}
