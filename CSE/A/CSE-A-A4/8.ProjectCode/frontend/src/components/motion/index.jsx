import { useEffect, useRef, useState } from 'react'
import {
  animate,
  motion,
  useInView,
  useMotionValue,
  useReducedMotion,
  useScroll,
  useSpring,
  useTransform,
} from 'framer-motion'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { softSpring, spring } from '../../lib/motion'

gsap.registerPlugin(ScrollTrigger)

/** Plain opacity fade. */
export function FadeIn({ children, delay = 0, duration = 0.5, className, as = 'div', ...rest }) {
  const M = motion[as]
  return (
    <M className={className} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration, delay }} {...rest}>
      {children}
    </M>
  )
}

/** Fade + rise on a spring (MotionConfig reducedMotion="user" collapses it to a fade). */
export function SlideUp({ children, delay = 0, y = 18, className, as = 'div', ...rest }) {
  const M = motion[as]
  return (
    <M
      className={className}
      initial={{ opacity: 0, y }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...softSpring, opacity: { duration: 0.45 }, delay }}
      {...rest}
    >
      {children}
    </M>
  )
}

const staggerParent = (gap, delay) => ({ hidden: {}, show: { transition: { staggerChildren: gap, delayChildren: delay } } })
const staggerChild = {
  hidden: { opacity: 0, y: 16, scale: 0.98 },
  show: { opacity: 1, y: 0, scale: 1, transition: { ...softSpring, opacity: { duration: 0.4 } } },
}

/** Children wrapped in <Stagger.Item> enter one after another. */
export function Stagger({ children, gap = 0.07, delay = 0, className, inView = false, as = 'div', ...rest }) {
  const M = motion[as]
  const trigger = inView ? { whileInView: 'show', viewport: { once: true, margin: '-60px' } } : { animate: 'show' }
  return (
    <M className={className} variants={staggerParent(gap, delay)} initial="hidden" {...trigger} {...rest}>
      {children}
    </M>
  )
}
Stagger.Item = function StaggerItem({ children, className, as = 'div', ...rest }) {
  const M = motion[as]
  return (
    <M className={className} variants={staggerChild} {...rest}>
      {children}
    </M>
  )
}

/** GSAP ScrollTrigger reveal - a light fade-up as the element scrolls into view. */
export function Reveal({ children, className, y = 28, delay = 0, as: Tag = 'div', ...rest }) {
  const ref = useRef(null)
  const reduce = useReducedMotion()
  useEffect(() => {
    const el = ref.current
    if (!el) return undefined
    const ctx = gsap.context(() => {
      gsap.fromTo(
        el,
        { autoAlpha: 0, y: reduce ? 0 : y },
        {
          autoAlpha: 1,
          y: 0,
          duration: reduce ? 0.4 : 0.9,
          delay,
          ease: 'power2.out',
          scrollTrigger: { trigger: el, start: 'top 88%', once: true },
        },
      )
    }, el)
    return () => ctx.revert()
  }, [reduce, y, delay])
  return (
    <Tag ref={ref} className={className} {...rest}>
      {children}
    </Tag>
  )
}

/** Route-level enter/exit. */
export function PageTransition({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ ...softSpring, opacity: { duration: 0.3 } }}
    >
      {children}
    </motion.div>
  )
}

/** Wraps a control and gently pulls it toward the pointer. */
export function MagneticButton({ children, strength = 0.28, className }) {
  const ref = useRef(null)
  const reduce = useReducedMotion()
  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const sx = useSpring(x, { stiffness: 260, damping: 15, mass: 0.6 })
  const sy = useSpring(y, { stiffness: 260, damping: 15, mass: 0.6 })
  const move = (e) => {
    if (reduce || e.pointerType !== 'mouse') return
    const r = ref.current.getBoundingClientRect()
    x.set((e.clientX - (r.left + r.width / 2)) * strength)
    y.set((e.clientY - (r.top + r.height / 2)) * strength)
  }
  const leave = () => {
    x.set(0)
    y.set(0)
  }
  return (
    <motion.span
      ref={ref}
      className={className}
      style={{ display: 'inline-flex', x: sx, y: sy }}
      onPointerMove={move}
      onPointerLeave={leave}
    >
      {children}
    </motion.span>
  )
}

/** Counts up from 0 when scrolled into view. */
export function CountUp({ value, format = (v) => Math.round(v).toLocaleString('en-IN'), duration = 1.4, className }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-40px' })
  const reduce = useReducedMotion()
  const [shown, setShown] = useState(reduce ? value : 0)
  useEffect(() => {
    if (value == null || Number.isNaN(value)) return undefined
    if (reduce) {
      setShown(value)
      return undefined
    }
    if (!inView) return undefined
    const c = animate(0, value, { duration, ease: [0.16, 1, 0.3, 1], onUpdate: setShown })
    return () => c.stop()
  }, [inView, value, reduce, duration])
  return (
    <span ref={ref} className={className} aria-label={value == null ? undefined : format(value)}>
      <span aria-hidden="true">{value == null ? '–' : format(shown)}</span>
    </span>
  )
}

/** Endless horizontal ticker; pauses on hover, static under reduced motion. */
export function Marquee({ children, speed = 40, className }) {
  const reduce = useReducedMotion()
  const [paused, setPaused] = useState(false)
  if (reduce) {
    return (
      <div className={className} style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
        {children}
      </div>
    )
  }
  return (
    <div
      className={`marquee ${className || ''}`}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <div
        className="marquee-track"
        style={{ animation: `marquee ${speed}s linear infinite`, animationPlayState: paused ? 'paused' : 'running' }}
      >
        <div className="marquee-track" style={{ paddingRight: 12 }}>{children}</div>
        <div className="marquee-track" style={{ paddingRight: 12 }} aria-hidden="true">
          {children}
        </div>
      </div>
      <style>{'@keyframes marquee{from{transform:translateX(0)}to{transform:translateX(-50%)}}'}</style>
    </div>
  )
}

/** Moves children at a different rate to the scroll. */
export function Parallax({ children, offset = 60, className, style }) {
  const ref = useRef(null)
  const reduce = useReducedMotion()
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start end', 'end start'] })
  const y = useTransform(scrollYProgress, [0, 1], reduce ? [0, 0] : [-offset, offset])
  return (
    <motion.div ref={ref} className={className} style={{ ...style, y }}>
      {children}
    </motion.div>
  )
}

export { spring }
