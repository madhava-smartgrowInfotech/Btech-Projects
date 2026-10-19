import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Lenis from 'lenis'
import { ArrowRight, BarChart3, CalendarClock, CarFront, CreditCard, Gauge, LogIn, MapPin, Moon, Navigation, Search, ShieldCheck, Sun, Timer } from 'lucide-react'
import { BrandMark, Button, ErrorState, IconButton } from '../components/ui'
import { CountUp, MagneticButton, Marquee, Parallax, Reveal, SlideUp, Stagger, ScrollTrigger, gsap } from '../components/motion'
import HeroVisual from '../components/three/HeroVisual'
import { Api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useTheme } from '../lib/theme'
import { useAsync } from '../lib/useAsync'
import { useMediaQuery, useReducedMotion } from '../lib/motion'
import { defaultWindow, fromLocalInput, money } from '../lib/format'

const STEPS = [
  { id: 'search', num: '01', title: 'Search a time window', body: 'Pick when you arrive and leave. ParkSure counts the reservations that overlap your window and shows how many bays can still be booked at each location.' },
  { id: 'reserve', num: '02', title: 'Reserve and pay', body: 'The fee is hours times the location rate times your trust multiplier. Account credit is applied first, and the rest is paid by card or the built-in demo checkout.' },
  { id: 'checkin', num: '03', title: 'Check in on arrival', body: 'Tap Check in when you get there. If an overstay left the site physically full, the nearest location with space is booked for you automatically, by straight-line distance.' },
  { id: 'trust', num: '04', title: 'Check out on time, pay less', body: 'Leave within ten minutes of your window ending. Streaks of on-time checkouts raise your Trust Score, and a higher score lowers every future fee.' },
]

const FEATURES = [
  { icon: ShieldCheck, title: 'Smart availability buffer', body: 'Each location holds back a few bays. The buffer grows with every on-time checkout and resets daily, so overstays rarely strand anyone.' },
  { icon: Gauge, title: 'Trust-based pricing', body: 'A Trust Score from 0 to 5 sets your fee multiplier. Reliable drivers earn a discount; repeated late checkouts cost more.' },
  { icon: Navigation, title: 'Nearest alternate', body: 'When a site is full on arrival, exactly one nearest location with space is booked for you. If none has space, the fee is credited back.' },
  { icon: CalendarClock, title: 'Check in and out in the app', body: 'No hardware needed. Your booking moves from reserved to parked to completed with one tap each.' },
  { icon: CreditCard, title: 'Stripe or demo checkout', body: 'Stripe test mode when keys are set, otherwise a clearly labelled demo checkout so everything works offline.' },
  { icon: BarChart3, title: 'Strategy insights for operators', body: 'Admins replay real booking history under four buffer policies and see which one strands the fewest drivers.' },
]

// Lenis smooth scroll, wired to ScrollTrigger. Skipped entirely for reduced motion.
function useSmoothScroll(enabled) {
  useEffect(() => {
    if (!enabled) return undefined
    const lenis = new Lenis({ lerp: 0.1 })
    lenis.on('scroll', ScrollTrigger.update)
    const tick = (t) => lenis.raf(t * 1000)
    gsap.ticker.add(tick)
    gsap.ticker.lagSmoothing(0)
    return () => {
      gsap.ticker.remove(tick)
      lenis.destroy()
    }
  }, [enabled])
}

export default function Landing() {
  const reduced = useReducedMotion()
  useSmoothScroll(!reduced)
  const locs = useAsync(() => Api.locations(), [])
  const rows = locs.data || []
  const stats = useMemo(
    () => ({
      locations: rows.length,
      bays: rows.reduce((s, l) => s + l.capacity, 0),
      lowest: rows.length ? Math.min(...rows.map((l) => l.price_per_hour)) : 0,
      held: rows.reduce((s, l) => s + l.buffer_size, 0),
    }),
    [rows],
  )

  return (
    <div className="landing">
      <LandingNav />
      <main id="main">
        <Hero count={locs.data ? stats.locations : null} bays={stats.bays} />
        <Signals locs={locs} />
        <How rows={rows} />
        <section className="l-section" id="why">
          <div className="l-wrap">
            <Reveal className="section-head">
              <span className="eyebrow">Why ParkSure</span>
              <h2>Built so a full lot never ruins your day</h2>
            </Reveal>
            <Stagger className="feature-cards" inView>
              {FEATURES.map(({ icon: Icon, title, body }) => (
                <div key={title} style={{ display: 'flex', width: '100%' }}>
                  <div className="card spot feature-card">
                    <span className="feature-icon">
                      <Icon size={20} aria-hidden="true" />
                    </span>
                    <h3>{title}</h3>
                    <p>{body}</p>
                  </div>
                </div>
              ))}
            </Stagger>
          </div>
        </section>
        <Numbers stats={stats} loaded={!!locs.data} />
        <Cta />
      </main>
      <Footer />
    </div>
  )
}

function LandingNav() {
  const [scrolled, setScrolled] = useState(false)
  const { theme, toggle } = useTheme()
  const { user } = useAuth()
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 24)
    on()
    window.addEventListener('scroll', on, { passive: true })
    return () => window.removeEventListener('scroll', on)
  }, [])
  return (
    <header className={`l-nav${scrolled ? ' scrolled' : ''}`}>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <div className="l-wrap l-nav-inner">
        <Link to="/" className="brand">
          <BrandMark />
          <span>ParkSure</span>
        </Link>
        <nav className="l-nav-links" aria-label="Page sections">
          <a href="#locations">Locations</a>
          <a href="#how">How it works</a>
          <a href="#why">Why ParkSure</a>
        </nav>
        <div className="row" style={{ gap: 8 }}>
          <IconButton icon={theme === 'dark' ? Sun : Moon} label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggle} />
          {user ? (
            <Button as={Link} to={user.role === 'admin' ? '/app/admin' : '/app/find'} variant="primary" size="sm" iconRight={ArrowRight}>
              Open app
            </Button>
          ) : (
            <>
              <Button as={Link} to="/login" variant="ghost" size="sm" icon={LogIn} className="hide-sm">
                Log in
              </Button>
              <Button as={Link} to="/login" state={{ from: '/app/find' }} variant="primary" size="sm">
                Get started
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}

function Hero({ count, bays }) {
  const nav = useNavigate()
  const [{ start, end }, setWin] = useState(defaultWindow)
  const [err, setErr] = useState('')
  const submit = (e) => {
    e.preventDefault()
    if (!start || !end || new Date(end) <= new Date(start)) {
      setErr('Departure must be after arrival.')
      return
    }
    nav(`/app/find?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`)
  }
  return (
    <section className="hero">
      <div className="hero-layer hero-grid" aria-hidden="true" />
      <div className="hero-layer hero-orbs" aria-hidden="true">
        <Parallax speed={0.5} className="orb orb-a" />
        <Parallax speed={-0.3} className="orb orb-b" />
      </div>
      <div className="hero-layer hero-visual">
        <HeroVisual />
      </div>
      <div className="l-wrap hero-inner">
        <div className="hero-copy">
          <SlideUp>
            <span className="eyebrow">
              <span className="pulse" aria-hidden="true" />
              {count === null ? 'Smart parking reservations' : `${count} locations, ${bays} bays, live`}
            </span>
          </SlideUp>
          <SlideUp delay={0.08}>
            <h1>
              Parking, reserved <span className="text-grad">before you arrive.</span>
            </h1>
          </SlideUp>
          <SlideUp delay={0.16}>
            <p className="hero-sub">Search real availability, reserve a bay in advance and check in from your phone. A hold-back buffer and a driver Trust Score keep every location reliable.</p>
          </SlideUp>
          <SlideUp delay={0.24}>
            <form className="hero-form" onSubmit={submit} aria-label="Find parking">
              <CalendarClock className="hero-form-icon" size={18} aria-hidden="true" />
              <label className="sr-only" htmlFor="h-start">Arrival</label>
              <input id="h-start" type="datetime-local" value={start} onChange={(e) => { setWin((w) => ({ ...w, start: e.target.value })); setErr('') }} />
              <label className="sr-only" htmlFor="h-end">Departure</label>
              <input id="h-end" type="datetime-local" value={end} min={start} onChange={(e) => { setWin((w) => ({ ...w, end: e.target.value })); setErr('') }} />
              <MagneticButton>
                <Button type="submit" variant="primary" icon={Search}>
                  Search
                </Button>
              </MagneticButton>
            </form>
            {err && (
              <p className="field-error" role="alert" style={{ marginTop: 8 }}>
                {err}
              </p>
            )}
          </SlideUp>
          <SlideUp delay={0.32}>
            <div className="hero-meta">
              <span>
                <ShieldCheck size={14} aria-hidden="true" /> No surprise fees
              </span>
              <span>
                <Timer size={14} aria-hidden="true" /> Check in and out in the app
              </span>
              <span>
                <Gauge size={14} aria-hidden="true" /> Earn a discount for being on time
              </span>
            </div>
          </SlideUp>
        </div>
      </div>
      <div className="scroll-cue" aria-hidden="true">
        <span />
      </div>
    </section>
  )
}

function Signals({ locs }) {
  const rows = locs.data
  return (
    <section className="signals" id="locations" aria-label="Locations">
      {locs.error ? (
        <div className="l-wrap">
          <ErrorState title="Locations could not load" error={locs.error} onRetry={() => locs.reload()} />
        </div>
      ) : !rows ? (
        <div className="signals-empty" aria-busy="true" aria-label="Loading locations" />
      ) : rows.length === 0 ? (
        <p className="muted" style={{ textAlign: 'center' }}>No locations have been added yet.</p>
      ) : (
        <>
          <Marquee label="Parking locations" speed={36}>
            {rows.map((l) => (
              <span key={l.id} className="signal">
                <MapPin size={12} aria-hidden="true" style={{ display: 'inline', verticalAlign: '-1px' }} /> {l.name} · {l.capacity} bays · {money(l.price_per_hour)}/h
              </span>
            ))}
          </Marquee>
          <Marquee label="Parking addresses" speed={46} reverse>
            {rows.map((l) => (
              <span key={l.id} className="signal">
                {l.address || l.name}
              </span>
            ))}
          </Marquee>
        </>
      )}
    </section>
  )
}

const LADDER = [
  { score: 5, mult: 0.9 },
  { score: 4, mult: 0.95 },
  { score: 3, mult: 1.0 },
  { score: 2, mult: 1.25 },
  { score: 1, mult: 1.5 },
  { score: 0, mult: 1.75 },
]

function HowVisual({ id, rows }) {
  const sample = rows[0]
  if (id === 'search')
    return (
      <>
        <div className="viz-label">Capacity by location</div>
        {rows.length === 0 ? (
          <p className="muted">Locations appear here once an admin adds them.</p>
        ) : (
          <div className="viz-bars">
            {rows.slice(0, 4).map((l, i) => {
              const max = Math.max(...rows.map((r) => r.capacity))
              return (
                <div key={l.id} className={`viz-bar${i === 0 ? ' best' : ''}`}>
                  <div className="row" style={{ justifyContent: 'space-between' }}>
                    <span>{l.name}</span>
                    <span className="mono">{l.capacity} bays</span>
                  </div>
                  <div className="viz-track">
                    <i style={{ width: `${(l.capacity / max) * 100}%` }} />
                  </div>
                </div>
              )
            })}
          </div>
        )}
        <div className="viz-foot">Real locations from the ParkSure database.</div>
      </>
    )
  if (id === 'reserve')
    return (
      <>
        <div className="viz-label">How the fee is made</div>
        <div className="anatomy-url mono">hours × {sample ? `${money(sample.price_per_hour)}/h` : 'rate'} × trust multiplier</div>
        <ul className="anatomy-list">
          <li><span className="anatomy-tag">Hours</span> Your window, at least 15 minutes</li>
          <li><span className="anatomy-tag">Rate</span> {sample ? `${sample.name} charges ${money(sample.price_per_hour)} per hour` : 'Each location sets its own rate'}</li>
          <li><span className="anatomy-tag">Multiplier</span> From x0.90 to x1.75 by Trust Score</li>
          <li><span className="anatomy-tag">Credit</span> Used first, automatically</li>
        </ul>
      </>
    )
  if (id === 'checkin')
    return (
      <>
        <div className="viz-label">On arrival</div>
        <div className="viz-stats">
          <div><strong>1</strong><span>Space free: you park</span></div>
          <div><strong>2</strong><span>Full: nearest alternate</span></div>
          <div><strong>3</strong><span>None: fee credited</span></div>
        </div>
        <div className="viz-foot">The alternate is chosen by haversine distance between stored coordinates.</div>
      </>
    )
  return (
    <>
      <div className="viz-label">Fee multiplier by Trust Score</div>
      <div className="viz-bars">
        {LADDER.map((r) => (
          <div key={r.score} className={`viz-bar${r.score === 5 ? ' best' : ''}`}>
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <span>Score {r.score}</span>
              <span className="mono">x{r.mult.toFixed(2)}</span>
            </div>
            <div className="viz-track">
              <i style={{ width: `${(r.mult / 1.75) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </>
  )
}

function How({ rows }) {
  const [active, setActive] = useState(0)
  const root = useRef(null)
  const bar = useRef(null)
  const reduced = useReducedMotion()
  const narrow = useMediaQuery('(max-width: 900px)')

  useEffect(() => {
    const el = root.current
    if (!el) return undefined
    const ctx = gsap.context(() => {
      el.querySelectorAll('.how-step').forEach((step, i) => {
        ScrollTrigger.create({ trigger: step, start: 'top 55%', end: 'bottom 55%', onToggle: (s) => s.isActive && setActive(i) })
      })
      if (bar.current && !reduced)
        gsap.fromTo(bar.current, { scaleY: 0 }, { scaleY: 1, ease: 'none', scrollTrigger: { trigger: el.querySelector('.how-copy'), start: 'top 60%', end: 'bottom 60%', scrub: true } })
    }, el)
    return () => ctx.revert()
  }, [reduced, narrow])

  return (
    <section className="how" id="how" ref={root}>
      <div className="l-wrap">
        <Reveal className="section-head">
          <span className="eyebrow">How it works</span>
          <h2>From search to saved money, in four steps</h2>
        </Reveal>
        <div className="how-grid">
          <div className="how-copy">
            <div className="how-progress" aria-hidden="true">
              <i ref={bar} style={reduced ? undefined : undefined} />
            </div>
            {STEPS.map((s) => (
              <article key={s.id} className="how-step">
                <span className="how-num mono">{s.num}</span>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
                {narrow && (
                  <div className="card how-card inline">
                    <HowVisual id={s.id} rows={rows} />
                  </div>
                )}
              </article>
            ))}
          </div>
          {!narrow && (
            <div className="how-visual-col">
              <div className="how-visual">
                <div className="card how-card" aria-live="polite">
                  <div className="how-card-head">
                    <span className="mono faint">{STEPS[active].num} / 04</span>
                    <div className="dots" aria-hidden="true">
                      {STEPS.map((s, i) => (
                        <i key={s.id} className={i === active ? 'on' : ''} />
                      ))}
                    </div>
                  </div>
                  <HowVisual id={STEPS[active].id} rows={rows} />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

function Numbers({ stats, loaded }) {
  const items = [
    { label: 'Locations', value: stats.locations },
    { label: 'Parking bays', value: stats.bays },
    { label: 'Bays held back as buffer', value: stats.held },
    { label: 'Lowest hourly rate', value: stats.lowest, format: (v) => `$${v.toFixed(2)}` },
  ]
  return (
    <section className="numbers" aria-label="ParkSure in numbers">
      <div className="l-wrap">
        <div className="numbers-grid n4">
          {items.map((n) => (
            <div key={n.label} className="number">
              <strong>{loaded ? <CountUp value={n.value} format={n.format} /> : '-'}</strong>
              <span>{n.label}</span>
            </div>
          ))}
        </div>
        <p className="faint numbers-note">Counted live from the locations in the database.</p>
      </div>
    </section>
  )
}

function Cta() {
  const { user } = useAuth()
  return (
    <section className="l-section">
      <div className="l-wrap">
        <Reveal className="card cta-card">
          <div className="cta-glow" aria-hidden="true" />
          <h2>Ready to park smarter?</h2>
          <p>Create a free driver account, or try the seeded demo logins on the sign-in page.</p>
          <div className="row" style={{ justifyContent: 'center', marginTop: 28 }}>
            <MagneticButton>
              <Button as={Link} to={user ? '/app/find' : '/login'} variant="primary" size="lg" iconRight={ArrowRight}>
                {user ? 'Find parking' : 'Reserve a spot'}
              </Button>
            </MagneticButton>
            <Button as={Link} to="/login" size="lg" icon={CarFront}>
              Demo logins
            </Button>
          </div>
        </Reveal>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="l-footer">
      <div className="l-wrap">
        <div className="l-footer-inner">
          <div>
            <Link to="/" className="brand" style={{ padding: 0 }}>
              <BrandMark />
              <span>ParkSure</span>
            </Link>
            <p className="faint" style={{ marginTop: 10, maxWidth: '38ch' }}>Smart parking reservations with a hold-back buffer and trust-based pricing.</p>
          </div>
          <nav className="l-footer-links" aria-label="Footer">
            <Link to="/app/find">Find parking</Link>
            <Link to="/app/bookings">My bookings</Link>
            <Link to="/app/trust">Trust score</Link>
            <Link to="/login">Log in</Link>
          </nav>
        </div>
        <div className="l-footer-base faint">ParkSure · Online Vehicle Parking Reservation System</div>
      </div>
    </footer>
  )
}
