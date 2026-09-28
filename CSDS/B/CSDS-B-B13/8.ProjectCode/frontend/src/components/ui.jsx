import { Loader2, AlertTriangle } from 'lucide-react'

export const SEV_STYLES = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  medium: 'bg-amber-100 text-amber-800 border-amber-200',
  low: 'bg-blue-100 text-blue-800 border-blue-200',
  info: 'bg-slate-100 text-slate-600 border-slate-200',
}

export function SeverityTag({ severity }) {
  return (
    <span className={`inline-block text-xs font-bold uppercase tracking-wide px-2 py-0.5
      rounded-full border ${SEV_STYLES[severity] || SEV_STYLES.info}`}>
      {severity}
    </span>
  )
}

export function Spinner({ label = 'Loading…' }) {
  return (
    <div className="flex items-center gap-2 text-slate-500 py-8 justify-center">
      <Loader2 className="animate-spin" size={18} /> {label}
    </div>
  )
}

export function ErrorBox({ message }) {
  if (!message) return null
  return (
    <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50
      text-red-700 px-3 py-2 text-sm my-2">
      <AlertTriangle size={16} className="mt-0.5 shrink-0" /> <span>{message}</span>
    </div>
  )
}

const GRADE_COLOR = {
  A: 'bg-green-600', B: 'bg-green-500', C: 'bg-amber-500',
  D: 'bg-orange-500', F: 'bg-red-600',
}

export function ScoreRing({ score, grade, size = 120 }) {
  const r = size / 2 - 8
  const circ = 2 * Math.PI * r
  const pct = Math.max(0, Math.min(100, score)) / 100
  const color = score >= 70 ? '#16a34a' : score >= 55 ? '#f59e0b'
    : score >= 35 ? '#f97316' : '#dc2626'
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="#e2e8f0" strokeWidth="8" fill="none" />
        <circle cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth="8" fill="none"
          strokeLinecap="round" strokeDasharray={circ}
          strokeDashoffset={circ * (1 - pct)} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-extrabold">{score}</span>
        <span className="text-xs text-slate-500">/ 100</span>
      </div>
    </div>
  )
}

export function GradeBadge({ grade }) {
  return (
    <span className={`inline-flex items-center justify-center w-12 h-12 rounded-xl
      text-white text-2xl font-extrabold ${GRADE_COLOR[grade] || 'bg-slate-400'}`}>
      {grade || '?'}
    </span>
  )
}
