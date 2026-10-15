import { Children, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { animate, motion, useInView, useMotionValue, useReducedMotion, useScroll, useSpring, useTransform } from 'framer-motion'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const EASE = [0.16, 1, 0.3, 1]

// All entrance motion collapses to a plain opacity fade when the user prefers reduced motion.
export function FadeIn({ children, delay = 0, duration = 0.6, as = 'div', ...rest }) {
  const M = motion[as]
  return (
    <M initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration, delay, ease: EASE }} {...rest}>
      {children}
    </M>
  )
}

export function SlideUp({ children, delay = 0, distance = 24, inView = false, as = 'div', ...rest }) {
  const reduced = useReducedMotion()
  const M = motion[as]
  const hidden = { opacity: 0, y: reduced ? 0 : distance }
  const shown = { opacity: 1, y: 0 }
  const trigger = inView ? { whileInView: shown, viewport: { once: true, margin: '-60px' } } : { animate: shown }
  return (
    <M initial={hidden} {...trigger} transition={{ duration: reduced ? 0.3 : 0.7, delay, ease: EASE }} {...rest}>
      {children}
    </M>
  )
}

export function Stagger({ children, gap = 0.07, delay = 0, inView = false, className, as = 'div', style }) {
  const reduced = useReducedMotion()
  const M = motion[as]
  const container = { hidden: {}, shown: { transition: { staggerChildren: reduced ? 0 : gap, delayChildren: delay } } }
  const item = {
    hidden: { opacity: 0, y: reduced ? 0 : 18 },
    shown: { opacity: 1, y: 0, transition: { duration: reduced ? 0.3 : 0.55, ease: EASE } },
  }
  const trigger = inView ? { whileInView: 'shown', viewport: { once: true, margin: '-40px' } } : { animate: 'shown' }
  return (
    <M className={className} style={style} variants={container} initial="hidden" {...trigger}>
      {Children.map(children, (child, i) =>
        child ? (
          <motion.div key={child.key ?? i} variants={item} style={{ minWidth: 0 }}>
            {child}
          </motion.div>
        ) : null,
      )}
    </M>
  )
}

// Scroll-triggered reveal driven by GSAP ScrollTrigger.
export function Reveal({ children, y = 48, delay = 0, className, as: As = 'div', ...rest }) {
  const ref = useRef(null)
  const reduced = useReducedMotion()
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return undefined
    const ctx = gsap.context(() => {
      gsap.fromTo(
        el,
        { autoAlpha: 0, y: reduced ? 0 : y },
        {
          autoAlpha: 1,
          y: 0,
          duration: reduced ? 0.4 : 1,
          delay,
          ease: 'expo.out',
          scrollTrigger: { trigger: el, start: 'top 88%', once: true },
        },
      )
    }, el)
    return () => ctx.revert()
  }, [reduced, y, delay])
  return (
    <As ref={ref} className={className} {...rest}>
      {children}
    </As>
  )
}

export function PageTransition({ children }) {
  const reduced = useReducedMotion()
  return (
    <motion.div
      initial={{ opacity: 0, y: reduced ? 0 : 14, filter: reduced ? 'none' : 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      exit={{ opacity: 0, y: reduced ? 0 : -8, filter: 'blur(0px)' }}
      transition={{ duration: reduced ? 0.2 : 0.4, ease: EASE }}
    >
      {children}
    </motion.div>
  )
}

// Wrapper that pulls its child toward the pointer.
export function MagneticButton({ children, strength = 0.35, className, style }) {
  const ref = useRef(null)
  const reduced = useReducedMotion()
  const x = useSpring(0, { stiffness: 220, damping: 16, mass: 0.4 })
  const y = useSpring(0, { stiffness: 220, damping: 16, mass: 0.4 })
  const move = (e) => {
    if (reduced || e.pointerType !== 'mouse') return
    const r = ref.current.getBoundingClientRect()
    x.set((e.clientX - (r.left + r.width / 2)) * strength)
    y.set((e.clientY - (r.top + r.height / 2)) * strength)
  }
  const leave = () => {
    x.set(0)
    y.set(0)
  }
  return (
    <motion.span ref={ref} className={className} style={{ display: 'inline-flex', x, y, ...style }} onPointerMove={move} onPointerLeave={leave}>
      {children}
    </motion.span>
  )
}

export function CountUp({ value, format = (v) => Math.round(v).toLocaleString(), duration = 1.4 }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-20px' })
  const reduced = useReducedMotion()
  const [shown, setShown] = useState(reduced ? value : 0)
  const from = useRef(0)
  useEffect(() => {
    if (!inView) return undefined
    if (reduced) {
      setShown(value)
      return undefined
    }
    const controls = animate(from.current, value, {
      duration,
      ease: EASE,
      onUpdate: (v) => setShown(v),
      onComplete: () => {
        from.current = value
      },
    })
    return () => {
      from.current = value
      controls.stop()
    }
  }, [inView, value, reduced, duration])
  return (
    <span ref={ref} aria-label={format(value)}>
      <span aria-hidden="true">{format(shown)}</span>
    </span>
  )
}

export function Marquee({ children, speed = 40, reverse = false, label }) {
  const reduced = useReducedMotion()
  return (
    <div className={`marquee${reduced ? ' static' : ''}`} aria-label={label} role={label ? 'region' : undefined}>
      <div className="marquee-track" style={{ animationDuration: `${speed}s`, animationDirection: reverse ? 'reverse' : 'normal' }}>
        <div className="marquee-group">{children}</div>
        {!reduced && (
          <div className="marquee-group" aria-hidden="true">
            {children}
          </div>
        )}
      </div>
    </div>
  )
}

// Moves its children at a different rate from the page scroll to create depth.
export function Parallax({ children, speed = 0.25, className, style }) {
  const ref = useRef(null)
  const reduced = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start end', 'end start'] })
  const range = 220 * speed
  const y = useTransform(scrollYProgress, [0, 1], [range, -range])
  const still = useMotionValue(0)
  return (
    <motion.div ref={ref} className={className} style={{ ...style, y: reduced ? still : y }}>
      {children}
    </motion.div>
  )
}

export { gsap, ScrollTrigger }
