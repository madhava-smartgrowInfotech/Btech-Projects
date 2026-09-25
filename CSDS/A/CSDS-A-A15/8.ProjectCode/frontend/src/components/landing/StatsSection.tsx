import { useEffect, useState } from 'react'
import { AnimatedCounter } from '@/components/effects/AnimatedCounter'
import { publicApi } from '@/lib/api'

export function StatsSection() {
  const [accuracy, setAccuracy] = useState<number | null>(null)
  const [classes, setClasses] = useState(6)

  useEffect(() => {
    publicApi
      .modelInfo()
      .then((info) => {
        setClasses(info.defect_classes)
        if (info.test_accuracy) setAccuracy(info.test_accuracy * 100)
      })
      .catch(() => {})
  }, [])

  const stats = [
    { value: accuracy ?? 0, decimals: 1, suffix: '%', label: 'Held-out test accuracy', show: accuracy !== null },
    { value: classes, decimals: 0, suffix: '', label: 'Defect categories recognized', show: true },
    { value: 1, decimals: 0, suffix: 's', label: 'Median inspection turnaround', show: true },
    { value: 100, decimals: 0, suffix: '%', label: 'Reports generated automatically', show: true },
  ]

  return (
    <section id="performance" className="relative py-24 border-t border-white/5">
      <div className="mx-auto max-w-7xl px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats
            .filter((s) => s.show)
            .map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="font-display text-4xl md:text-5xl font-bold text-gradient">
                  <AnimatedCounter value={stat.value} decimals={stat.decimals} suffix={stat.suffix} />
                </div>
                <p className="mt-2 text-sm text-slate-500">{stat.label}</p>
              </div>
            ))}
        </div>
      </div>
    </section>
  )
}
