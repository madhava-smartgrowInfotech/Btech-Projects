import confetti from 'canvas-confetti'

const fired = new Set()

/** One gentle pastel burst per kind of success per session - never repeated. */
export function celebrate(kind) {
  if (fired.has(kind)) return false
  fired.add(kind)
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return true
  confetti({
    particleCount: 90,
    spread: 75,
    startVelocity: 38,
    gravity: 0.9,
    scalar: 0.95,
    ticks: 220,
    origin: { y: 0.65 },
    colors: ['#C7B9FF', '#A7E8C8', '#FFC9A3', '#A9D6FF', '#FFE7A3'],
    disableForReducedMotion: true,
  })
  return true
}
