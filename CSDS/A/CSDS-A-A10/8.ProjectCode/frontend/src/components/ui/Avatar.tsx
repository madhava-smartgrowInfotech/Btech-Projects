import { initials } from '@/lib/utils'

export function Avatar({
  name,
  color = '#3b82f6',
  size = 36,
}: {
  name: string
  color?: string
  size?: number
}) {
  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-full font-display font-bold text-white"
      style={{
        width: size,
        height: size,
        fontSize: size * 0.38,
        background: `linear-gradient(135deg, ${color}, ${color}cc)`,
      }}
    >
      {initials(name)}
    </div>
  )
}
