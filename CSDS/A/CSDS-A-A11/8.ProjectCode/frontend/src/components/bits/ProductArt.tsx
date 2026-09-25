import { cn, artGradient, seedToUnit } from '@/lib/utils'

type Props = {
  seed?: string | number
  name?: string
  className?: string
  /** Larger variant adds more depth layers for the product detail gallery. */
  detail?: boolean
}

/**
 * Generated product artwork. Every item gets a deterministic studio-lit composition
 * derived from its seed — no external image fetching, and it never mismatches on reload.
 */
export function ProductArt({ seed, name, className, detail = false }: Props) {
  const key = seed ?? name ?? 'nuvara'
  const { css, hueA, hueB } = artGradient(key)
  const shape = seedToUnit(key, 7)
  const offsetX = 18 + seedToUnit(key, 11) * 30
  const offsetY = 20 + seedToUnit(key, 13) * 28
  const scale = 0.52 + seedToUnit(key, 17) * 0.24
  const rounded = shape > 0.66 ? '50%' : shape > 0.33 ? '28%' : '14%'

  return (
    <div
      className={cn('relative overflow-hidden bg-ink-850', className)}
      style={{ background: css }}
      aria-hidden
    >
      <div
        className="absolute rounded-full blur-2xl"
        style={{
          left: `${offsetX}%`,
          top: `${offsetY}%`,
          width: `${scale * 100}%`,
          aspectRatio: '1',
          transform: 'translate(-50%, -50%)',
          background: `radial-gradient(circle at 34% 30%, hsl(${hueB} 70% 74% / 0.9), hsl(${hueA} 58% 42% / 0.55) 42%, transparent 72%)`,
        }}
      />
      <div
        className="absolute border border-white/25"
        style={{
          left: `${offsetX}%`,
          top: `${offsetY}%`,
          width: `${scale * 74}%`,
          aspectRatio: shape > 0.5 ? '1' : '3 / 4',
          transform: `translate(-50%, -50%) rotate(${Math.round(seedToUnit(key, 19) * 24 - 12)}deg)`,
          borderRadius: rounded,
          background: `linear-gradient(150deg, hsl(${hueB} 34% 72% / 0.34), hsl(${hueA} 30% 18% / 0.7))`,
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.35), 0 30px 60px -24px rgba(0,0,0,0.8)',
          backdropFilter: 'blur(2px)',
        }}
      />
      {detail && (
        <div
          className="absolute inset-x-[14%] bottom-[12%] h-[8%] rounded-[50%] blur-xl"
          style={{ background: 'rgba(0,0,0,0.55)' }}
        />
      )}
      <div className="absolute inset-0 bg-[radial-gradient(120%_90%_at_50%_0%,rgba(255,255,255,0.09),transparent_60%)]" />
      <div className="noise absolute inset-0" />
    </div>
  )
}
