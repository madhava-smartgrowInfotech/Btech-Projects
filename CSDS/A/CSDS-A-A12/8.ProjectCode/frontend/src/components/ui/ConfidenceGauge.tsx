import { motion } from 'framer-motion'

interface ConfidenceGaugeProps {
  value: number // 0..1
  label?: string
  tone?: 'emerald' | 'amber' | 'danger'
  size?: number
}

const toneColors: Record<string, string> = {
  emerald: '#34d399',
  amber: '#fbbf24',
  danger: '#f87171',
}

export function ConfidenceGauge({ value, label = 'Confidence', tone = 'emerald', size = 180 }: ConfidenceGaugeProps) {
  const radius = size / 2 - 14
  const circumference = 2 * Math.PI * radius
  const pct = Math.max(0, Math.min(1, value))
  const offset = circumference * (1 - pct)
  const color = toneColors[tone]

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={10}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          style={{ filter: `drop-shadow(0 0 10px ${color}66)` }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <motion.span
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="font-display text-3xl font-bold"
        >
          {(pct * 100).toFixed(1)}%
        </motion.span>
        <span className="text-xs text-[var(--color-text-muted)] mt-1">{label}</span>
      </div>
    </div>
  )
}
