import { motion } from 'framer-motion'
import { Sprout, XCircle, TrendingUp, TrendingDown, Microscope, Lightbulb, Loader2 } from 'lucide-react'
import { Card } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { ConfidenceGauge } from '../ui/ConfidenceGauge'
import type { PredictionRecord } from '../../types'

interface ResultsPanelProps {
  result: PredictionRecord | null
  loading: boolean
  error: string | null
}

const riskTone: Record<string, 'emerald' | 'amber' | 'danger'> = {
  low: 'emerald',
  medium: 'amber',
  high: 'danger',
}

export function ResultsPanel({ result, loading, error }: ResultsPanelProps) {
  if (loading) {
    return (
      <Card className="h-full flex flex-col items-center justify-center gap-4 min-h-[480px]">
        <Loader2 className="animate-spin text-emerald-400" size={32} />
        <div className="text-center">
          <p className="text-sm font-medium">Encoding seed morphology…</p>
          <p className="text-xs text-[var(--color-text-faint)] mt-1">Fusing environmental signal and scoring batch</p>
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="h-full flex flex-col items-center justify-center gap-3 min-h-[480px] text-center">
        <XCircle className="text-red-400" size={32} />
        <p className="text-sm font-medium text-red-300">{error}</p>
        <p className="text-xs text-[var(--color-text-faint)] max-w-xs">
          Confirm the SeedIQ API is running at the configured endpoint and try again.
        </p>
      </Card>
    )
  }

  if (!result) {
    return (
      <Card className="h-full flex flex-col items-center justify-center gap-3 min-h-[480px] text-center">
        <Microscope className="text-[var(--color-text-faint)]" size={32} />
        <p className="text-sm font-medium text-[var(--color-text-muted)]">No prediction yet</p>
        <p className="text-xs text-[var(--color-text-faint)] max-w-xs">
          Upload a seed image and enter field conditions to run an analysis.
        </p>
      </Card>
    )
  }

  const isGerminate = result.prediction === 'germinate'

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-5">
      <Card glow className="flex flex-col sm:flex-row items-center gap-6">
        <ConfidenceGauge value={result.confidence} tone={isGerminate ? 'emerald' : 'danger'} />
        <div className="flex-1 text-center sm:text-left">
          <div className="flex items-center gap-2 justify-center sm:justify-start">
            {isGerminate ? (
              <Sprout className="text-emerald-400" size={20} />
            ) : (
              <XCircle className="text-red-400" size={20} />
            )}
            <h3 className="font-display text-xl font-bold">
              {isGerminate ? 'Likely to germinate' : 'Unlikely to germinate'}
            </h3>
          </div>
          <p className="text-sm text-[var(--color-text-muted)] mt-2 max-w-md">{result.explanation.summary}</p>
          <div className="flex flex-wrap gap-2 mt-4 justify-center sm:justify-start">
            <Badge tone={riskTone[result.risk_level]}>Risk: {result.risk_level}</Badge>
            <Badge tone="neutral">{result.seed_type}</Badge>
            <Badge tone="neutral">P(germinate) {(result.probability_germinate * 100).toFixed(0)}%</Badge>
          </div>
        </div>
      </Card>

      <Card>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-faint)] mb-4">
          Morphological traits
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <Trait label="Area" value={`${result.morphological_features.area.toFixed(1)} px²`} />
          <Trait label="Perimeter" value={`${result.morphological_features.perimeter.toFixed(1)} px`} />
          <Trait label="Aspect ratio" value={result.morphological_features.aspect_ratio.toFixed(2)} />
          <Trait label="Circularity" value={result.morphological_features.circularity.toFixed(2)} />
          <Trait
            label="Mean color"
            value={`rgb(${result.morphological_features.mean_color_rgb.map((c) => Math.round(c)).join(', ')})`}
            swatch={`rgb(${result.morphological_features.mean_color_rgb.join(',')})`}
          />
          <Trait label="Color std" value={result.morphological_features.color_std.toFixed(2)} />
        </div>
      </Card>

      <Card>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-faint)] mb-4 flex items-center gap-2">
          <Microscope size={13} /> Key factors
        </h4>
        <div className="flex flex-col gap-3">
          {result.explanation.key_factors.map((f) => (
            <div key={f.factor} className="flex items-start gap-3">
              {f.impact === 'positive' ? (
                <TrendingUp size={16} className="text-emerald-400 mt-0.5 shrink-0" />
              ) : (
                <TrendingDown size={16} className="text-red-400 mt-0.5 shrink-0" />
              )}
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{f.factor}</span>
                  <span className="text-xs text-[var(--color-text-faint)]">{(f.weight * 100).toFixed(0)}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-[var(--color-surface-2)] mt-1.5 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${f.weight * 100}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut' }}
                    className={`h-full rounded-full ${f.impact === 'positive' ? 'bg-emerald-400' : 'bg-red-400'}`}
                  />
                </div>
                <p className="text-xs text-[var(--color-text-faint)] mt-1.5">{f.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-faint)] mb-4 flex items-center gap-2">
          <Lightbulb size={13} /> Recommendations
        </h4>
        <ul className="flex flex-col gap-2.5">
          {result.explanation.recommendations.map((r, i) => (
            <li key={i} className="flex items-start gap-2.5 text-sm text-[var(--color-text-muted)]">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
              {r}
            </li>
          ))}
        </ul>
      </Card>
    </motion.div>
  )
}

function Trait({ label, value, swatch }: { label: string; value: string; swatch?: string }) {
  return (
    <div className="rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border-soft)] px-3.5 py-3">
      <span className="text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">{label}</span>
      <div className="flex items-center gap-2 mt-1">
        {swatch && <span className="w-3 h-3 rounded-full border border-white/10 shrink-0" style={{ background: swatch }} />}
        <span className="text-sm font-medium font-display truncate">{value}</span>
      </div>
    </div>
  )
}
