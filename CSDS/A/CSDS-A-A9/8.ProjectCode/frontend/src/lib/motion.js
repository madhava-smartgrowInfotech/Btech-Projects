// Shared spring presets - a gentle overshoot, never a snap.
export const spring = { type: 'spring', stiffness: 420, damping: 20, mass: 0.8 }
export const softSpring = { type: 'spring', stiffness: 240, damping: 22 }
export const press = { whileHover: { scale: 1.03, y: -1 }, whileTap: { scale: 0.95 }, transition: spring }
export const lift = { whileHover: { y: -5, scale: 1.01 }, whileTap: { scale: 0.985 }, transition: softSpring }
