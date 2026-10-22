/* Motion kit — GSAP (+ScrollTrigger), Lenis and Framer Motion, all collapsing to a plain fade
   when the user prefers reduced motion. */
import { Children, createContext, useContext, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { motion, useMotionValue, useSpring } from 'framer-motion'
import Lenis from 'lenis'
import { gsap, ScrollTrigger } from '../../lib/gsap'
import { prefersReducedMotion, useReducedMotion } from '../../lib/motion'

/* ------------------------------------------------------------ smooth scroll */
const LenisCtx = createContext(null)
export const useLenis = () => useContext(LenisCtx)

export function SmoothScroll({ children }) {
  const reduced = useReducedMotion()
  const [lenis, setLenis] = useState(null)
  useEffect(() => {
    if (reduced) return undefined
    const l = new Lenis({ lerp: 0.12, wheelMultiplier: 1 })
    const tick = (t) => l.raf(t * 1000)
    l.on('scroll', ScrollTrigger.update)
    gsap.ticker.add(tick)
    gsap.ticker.lagSmoothing(0)
    setLenis(l)
    return () => {
      gsap.ticker.remove(tick)
      l.destroy()
      setLenis(null)
    }
  }, [reduced])
  return <LenisCtx.Provider value={lenis}>{children}</LenisCtx.Provider>
}

/* ------------------------------------------------------------ framer basics */
export function FadeIn({ children, delay = 0, className, as = 'div', ...rest }) {
  const M = motion[as]
  return (
    <M
      className={className}
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ duration: 0.5, delay }}
      {...rest}
    >
      {children}
    </M>
  )
}

export function SlideUp({ children, delay = 0, y = 28, className, as = 'div', ...rest }) {
  const M = motion[as]
  return (
    <M
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ duration: 0.55, delay, ease: [0.2, 0.9, 0.1, 1] }}
      {...rest}
    >
      {children}
    </M>
  )
}

const staggerParent = { hidden: {}, show: { transition: { staggerChildren: 0.07 } } }
const staggerChild = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: [0.2, 0.9, 0.1, 1] } },
}

export function Stagger({ children, className, style, inView = true }) {
  return (
    <motion.div
      className={className}
      style={style}
      variants={staggerParent}
      initial="hidden"
      {...(inView ? { whileInView: 'show', viewport: { once: true, margin: '-40px' } } : { animate: 'show' })}
    >
      {Children.map(children, (c) => c && <motion.div variants={staggerChild} style={{ minWidth: 0 }}>{c}</motion.div>)}
    </motion.div>
  )
}

export function PageTransition({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.2, 0.9, 0.1, 1] }}
    >
      {children}
    </motion.div>
  )
}

/* ------------------------------------------------------------ GSAP effects */
function useGsap(fn, deps) {
  const ref = useRef(null)
  useLayoutEffect(() => {
    if (!ref.current) return undefined
    const ctx = gsap.context(() => fn(ref.current, prefersReducedMotion()), ref)
    return () => ctx.revert()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  return ref
}

/** Scroll-triggered reveal (ScrollTrigger). */
export function Reveal({ children, className, y = 48, delay = 0, as: Tag = 'div', style }) {
  const ref = useGsap(
    (el, reduced) => {
      gsap.from(el, {
        opacity: 0,
        y: reduced ? 0 : y,
        duration: reduced ? 0.3 : 0.9,
        delay,
        ease: 'power3.out',
        scrollTrigger: { trigger: el, start: 'top 90%', once: true },
      })
    },
    [y, delay],
  )
  return (
    <Tag ref={ref} className={className} style={style}>
      {children}
    </Tag>
  )
}

/** Oversized headline revealed line-by-line behind a mask (SplitText-style, manual lines). */
export function MaskHeadline({ lines, as: Tag = 'h1', className = '', delay = 0.1, scroll = false }) {
  const ref = useGsap(
    (el, reduced) => {
      const inner = el.querySelectorAll('.mask-line > span')
      const trigger = scroll ? { trigger: el, start: 'top 85%', once: true } : undefined
      if (reduced) {
        gsap.from(inner, { opacity: 0, duration: 0.4, delay, scrollTrigger: trigger })
        return
      }
      gsap.from(inner, {
        yPercent: 115,
        rotate: 2,
        duration: 1,
        ease: 'power4.out',
        stagger: 0.11,
        delay,
        scrollTrigger: trigger,
      })
    },
    [lines.join('|'), delay, scroll],
  )
  return (
    <Tag ref={ref} className={className} aria-label={lines.join(' ')}>
      {lines.map((l, i) => (
        <span className="mask-line" key={i} aria-hidden="true">
          <span>{l}</span>
        </span>
      ))}
    </Tag>
  )
}

/** Section divider: a thick ink rule that wipes in on scroll. */
export function InkRule({ thick = false, className = '', style }) {
  const ref = useGsap((el, reduced) => {
    if (reduced) {
      gsap.from(el, { opacity: 0, duration: 0.4, scrollTrigger: { trigger: el, start: 'top 95%', once: true } })
      return
    }
    gsap.fromTo(
      el,
      { scaleX: 0 },
      { scaleX: 1, duration: 1.1, ease: 'power3.inOut', scrollTrigger: { trigger: el, start: 'top 95%', once: true } },
    )
  }, [])
  return <div ref={ref} role="separator" className={`ink-rule ${thick ? 'thick' : ''} ${className}`} style={style} />
}

/** Scroll-linked parallax drift. */
export function Parallax({ children, speed = 0.15, className, style }) {
  const ref = useGsap(
    (el, reduced) => {
      if (reduced) return
      gsap.fromTo(
        el,
        { yPercent: speed * 60 },
        { yPercent: -speed * 60, ease: 'none', scrollTrigger: { trigger: el, start: 'top bottom', end: 'bottom top', scrub: true } },
      )
    },
    [speed],
  )
  return (
    <div ref={ref} className={className} style={style}>
      {children}
    </div>
  )
}

/** Number that counts up when it scrolls into view. */
export function CountUp({ value, decimals = 0, duration = 1.4, className, suffix = '' }) {
  const ref = useRef(null)
  const target = Number(value) || 0
  const [shown, setShown] = useState(() => (prefersReducedMotion() ? target : 0))
  useEffect(() => {
    if (prefersReducedMotion()) {
      setShown(target)
      return undefined
    }
    const el = ref.current
    if (!el) return undefined
    const obj = { v: 0 }
    let tween
    const io = new IntersectionObserver(
      ([e]) => {
        if (!e.isIntersecting) return
        io.disconnect()
        tween = gsap.to(obj, { v: target, duration, ease: 'power3.out', onUpdate: () => setShown(obj.v) })
      },
      { threshold: 0.3 },
    )
    io.observe(el)
    return () => {
      io.disconnect()
      tween?.kill()
    }
  }, [target, duration])
  return (
    <span ref={ref} className={className}>
      {shown.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}
      {suffix}
    </span>
  )
}

/** Endless ticker strip. Items: [{label, value}] — pauses on hover, static under reduced motion. */
export function Marquee({ items, variant = 'ink', label = 'Live statistics', speed = 6 }) {
  if (!items || !items.length) return null
  const dur = `${Math.max(18, items.length * speed)}s`
  const group = (hidden) => (
    <div className="marquee-group" aria-hidden={hidden || undefined}>
      {items.map((it, i) => (
        <span className="marquee-item" key={i}>
          {it.label} <strong>{it.value}</strong>
        </span>
      ))}
    </div>
  )
  return (
    <div className={`marquee ${variant === 'lime' ? 'lime' : ''}`} role="marquee" aria-label={label}>
      <div className="marquee-track" style={{ '--dur': dur }}>
        {group(false)}
        {group(true)}
      </div>
    </div>
  )
}

/** Button wrapper that leans toward the pointer. */
export function MagneticButton({ children, strength = 0.3 }) {
  const reduced = useReducedMotion()
  const x = useSpring(useMotionValue(0), { stiffness: 260, damping: 18 })
  const y = useSpring(useMotionValue(0), { stiffness: 260, damping: 18 })
  const onMove = (e) => {
    if (reduced) return
    const r = e.currentTarget.getBoundingClientRect()
    x.set((e.clientX - r.left - r.width / 2) * strength)
    y.set((e.clientY - r.top - r.height / 2) * strength)
  }
  const reset = () => {
    x.set(0)
    y.set(0)
  }
  return (
    <motion.span style={{ x, y, display: 'inline-flex' }} onPointerMove={onMove} onPointerLeave={reset}>
      {children}
    </motion.span>
  )
}

/** A hard-edged highlight block that chases the cursor across an interactive card. */
export function CursorHighlight({ children, className = '', as = 'div', size = 110, ...rest }) {
  const reduced = useReducedMotion()
  const mx = useMotionValue(-200)
  const my = useMotionValue(-200)
  const x = useSpring(mx, { stiffness: 420, damping: 32 })
  const y = useSpring(my, { stiffness: 420, damping: 32 })
  const Tag = as
  const onMove = (e) => {
    const r = e.currentTarget.getBoundingClientRect()
    mx.set(e.clientX - r.left - size / 2)
    my.set(e.clientY - r.top - size / 2)
  }
  return (
    <Tag className={`hot ${className}`} onPointerMove={reduced ? undefined : onMove} {...rest}>
      {!reduced && <motion.span aria-hidden="true" className="hot-block" style={{ x, y, width: size, height: size }} />}
      {children}
    </Tag>
  )
}
