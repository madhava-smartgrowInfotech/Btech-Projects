import { motion, useMotionValue, useSpring } from 'framer-motion'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { Children, useEffect, useLayoutEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { useReducedMotion } from '../../lib/reduced'

gsap.registerPlugin(ScrollTrigger)
const EASE = [0.2, 0.8, 0.2, 1]

// With reduced motion every entrance collapses to a plain opacity fade.
export function FadeIn({ children, delay = 0, duration = 0.45, className, as = 'div' }) {
  const M = motion[as]
  return (
    <M className={className} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration, delay, ease: EASE }}>
      {children}
    </M>
  )
}

export function SlideUp({ children, delay = 0, y = 16, className, as = 'div' }) {
  const reduced = useReducedMotion()
  const M = motion[as]
  return (
    <M className={className} initial={{ opacity: 0, y: reduced ? 0 : y }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: reduced ? 0.3 : 0.55, delay, ease: EASE }}>
      {children}
    </M>
  )
}

export function Stagger({ children, className, gap = 0.06, delay = 0, y = 14, as = 'div' }) {
  const reduced = useReducedMotion()
  const M = motion[as]
  const item = { hidden: { opacity: 0, y: reduced ? 0 : y }, show: { opacity: 1, y: 0, transition: { duration: reduced ? 0.3 : 0.5, ease: EASE } } }
  return (
    <M className={className} initial="hidden" animate="show"
      variants={{ show: { transition: { staggerChildren: reduced ? 0 : gap, delayChildren: delay } } }}>
      {Children.map(children, (c) => (c ? <motion.div variants={item} className="min-w-0">{c}</motion.div> : c))}
    </M>
  )
}

// Scroll-triggered reveal (GSAP ScrollTrigger). `stagger` reveals direct children in turn.
export function Reveal({ children, className, y = 32, delay = 0, stagger = 0, as: Tag = 'div', ...rest }) {
  const ref = useRef(null)
  const reduced = useReducedMotion()
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    const ctx = gsap.context(() => {
      gsap.from(stagger ? el.children : el, {
        opacity: 0, y: reduced ? 0 : y, duration: reduced ? 0.4 : 0.9, ease: 'power3.out', delay,
        stagger: reduced ? 0 : stagger, scrollTrigger: { trigger: el, start: 'top 88%', once: true },
      })
    }, el)
    return () => ctx.revert()
  }, [reduced, y, delay, stagger])
  return <Tag ref={ref} className={className} {...rest}>{children}</Tag>
}

export function Parallax({ children, speed = 0.2, className }) {
  const ref = useRef(null)
  const reduced = useReducedMotion()
  useLayoutEffect(() => {
    if (reduced || !ref.current) return
    const ctx = gsap.context(() => {
      gsap.to(ref.current, { yPercent: -100 * speed, ease: 'none', scrollTrigger: { trigger: ref.current, start: 'top bottom', end: 'bottom top', scrub: true } })
    }, ref)
    return () => ctx.revert()
  }, [reduced, speed])
  return <div ref={ref} className={className}>{children}</div>
}

export function PageTransition({ children }) {
  const { pathname } = useLocation()
  const reduced = useReducedMotion()
  return (
    <motion.div key={pathname} initial={{ opacity: 0, y: reduced ? 0 : 10 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: reduced ? 0.25 : 0.4, ease: EASE }}>
      {children}
    </motion.div>
  )
}

export function MagneticButton({ children, strength = 0.3, className = '' }) {
  const reduced = useReducedMotion()
  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const sx = useSpring(x, { stiffness: 260, damping: 18 })
  const sy = useSpring(y, { stiffness: 260, damping: 18 })
  function move(e) {
    if (reduced) return
    const r = e.currentTarget.getBoundingClientRect()
    x.set((e.clientX - r.left - r.width / 2) * strength)
    y.set((e.clientY - r.top - r.height / 2) * strength)
  }
  const reset = () => { x.set(0); y.set(0) }
  return (
    <motion.span className={`inline-block ${className}`} style={{ x: sx, y: sy }} onPointerMove={move} onPointerLeave={reset}>
      {children}
    </motion.span>
  )
}

// Animated number. Writes straight to the DOM so React re-renders never fight the tween.
export function CountUp({ value, format = (v) => Math.round(v).toLocaleString('en-IN'), duration = 1.3, className = '' }) {
  const ref = useRef(null)
  const from = useRef(0)
  const fmt = useRef(format)
  fmt.current = format
  const reduced = useReducedMotion()
  useEffect(() => {
    const el = ref.current
    if (!el) return
    if (reduced || typeof value !== 'number' || !Number.isFinite(value)) {
      el.textContent = typeof value === 'number' ? fmt.current(value) : String(value ?? '-')
      from.current = value
      return
    }
    const obj = { v: from.current || 0 }
    el.textContent = fmt.current(obj.v)
    const tw = gsap.to(obj, {
      v: value, duration, ease: 'power3.out',
      onUpdate: () => { el.textContent = fmt.current(obj.v) },
      onComplete: () => { from.current = value; el.textContent = fmt.current(value) },
    })
    return () => { tw.kill(); from.current = obj.v }
  }, [value, duration, reduced])
  return <span ref={ref} className={`tabular-nums ${className}`} />
}

export function Marquee({ children, duration = 40, className = '' }) {
  return (
    <div className={`marquee overflow-hidden ${className}`} style={{ '--marquee-duration': `${duration}s` }}>
      <div className="marquee-track flex w-max">
        <div className="flex shrink-0">{children}</div>
        <div className="flex shrink-0" aria-hidden="true">{children}</div>
      </div>
    </div>
  )
}
