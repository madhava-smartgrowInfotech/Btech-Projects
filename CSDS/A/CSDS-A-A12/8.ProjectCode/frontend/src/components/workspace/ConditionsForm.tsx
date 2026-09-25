import type { SeedType } from '../../types'

export interface Conditions {
  soil_moisture: number
  temperature: number
  humidity: number
  rainfall: number
  soil_ph: number
  seed_type: SeedType
}

interface ConditionsFormProps {
  values: Conditions
  onChange: (values: Conditions) => void
}

const seedTypes: SeedType[] = [
  'Pearl Millet',
  'Finger Millet',
  'Foxtail Millet',
  'Little Millet',
  'Kodo Millet',
  'Proso Millet',
  'Barnyard Millet',
]

const sliders: { key: keyof Conditions; label: string; min: number; max: number; step: number; unit: string }[] = [
  { key: 'soil_moisture', label: 'Soil moisture', min: 0, max: 100, step: 1, unit: '%' },
  { key: 'temperature', label: 'Temperature', min: -5, max: 50, step: 0.5, unit: '°C' },
  { key: 'humidity', label: 'Humidity', min: 0, max: 100, step: 1, unit: '%' },
  { key: 'rainfall', label: 'Rainfall (7-day)', min: 0, max: 300, step: 1, unit: 'mm' },
  { key: 'soil_ph', label: 'Soil pH', min: 3, max: 10, step: 0.1, unit: '' },
]

export function ConditionsForm({ values, onChange }: ConditionsFormProps) {
  function update<K extends keyof Conditions>(key: K, val: Conditions[K]) {
    onChange({ ...values, [key]: val })
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <label className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide">
          Seed variety
        </label>
        <select
          value={values.seed_type}
          onChange={(e) => update('seed_type', e.target.value as SeedType)}
          className="mt-2 w-full rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border)] px-3.5 py-2.5 text-sm focus:outline-none focus:border-emerald-500/60 transition-colors"
        >
          {seedTypes.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      {sliders.map((s) => (
        <div key={s.key}>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide">
              {s.label}
            </label>
            <span className="text-sm font-semibold text-emerald-300 font-display">
              {values[s.key]}
              {s.unit}
            </span>
          </div>
          <input
            type="range"
            min={s.min}
            max={s.max}
            step={s.step}
            value={values[s.key] as number}
            onChange={(e) => update(s.key, Number(e.target.value) as any)}
            className="w-full accent-emerald-400 cursor-pointer"
          />
        </div>
      ))}
    </div>
  )
}
