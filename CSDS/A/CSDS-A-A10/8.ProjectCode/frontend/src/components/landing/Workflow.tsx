import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { ClipboardCheck, FlaskConical, LogOut, Stethoscope, TicketCheck } from 'lucide-react'

gsap.registerPlugin(ScrollTrigger)

const STEPS = [
  {
    icon: TicketCheck,
    title: 'Register & tokenise',
    description: 'Reception logs the patient once — a digital token and department queue position are generated instantly.',
  },
  {
    icon: Stethoscope,
    title: 'AI-prioritised consultation',
    description: 'Vitals are scored in real time; critical and urgent patients are surfaced to doctors automatically.',
  },
  {
    icon: FlaskConical,
    title: 'Lab & pharmacy, in sync',
    description: 'Ordered tests appear on the lab queue immediately, and results flow back into the same patient timeline.',
  },
  {
    icon: ClipboardCheck,
    title: 'Ward & ICU admission',
    description: 'Nurses see live bed availability and admit patients with one action — no phone calls between floors.',
  },
  {
    icon: LogOut,
    title: 'Discharge & analytics',
    description: 'Every visit closes with a full movement record, feeding hospital-wide wait-time analytics.',
  },
]

export function Workflow() {
  const sectionRef = useRef<HTMLDivElement>(null)
  const lineRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(
        lineRef.current,
        { scaleY: 0 },
        {
          scaleY: 1,
          transformOrigin: 'top',
          ease: 'none',
          scrollTrigger: {
            trigger: sectionRef.current,
            start: 'top 70%',
            end: 'bottom 80%',
            scrub: 0.6,
          },
        },
      )

      gsap.utils.toArray<HTMLElement>('.workflow-step').forEach((step) => {
        gsap.fromTo(
          step,
          { opacity: 0, x: -24 },
          {
            opacity: 1,
            x: 0,
            duration: 0.6,
            ease: 'power2.out',
            scrollTrigger: { trigger: step, start: 'top 82%' },
          },
        )
      })
    }, sectionRef)

    return () => ctx.revert()
  }, [])

  return (
    <section id="workflow" ref={sectionRef} className="relative py-28">
      <div className="mx-auto max-w-4xl px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-vital-400">Workflow</p>
          <h2 className="mt-3 font-display text-3xl font-bold text-white sm:text-4xl text-balance">
            One continuous patient journey
          </h2>
        </div>

        <div className="relative mt-16 pl-14">
          <div className="absolute left-5 top-0 h-full w-px bg-white/10" />
          <div ref={lineRef} className="absolute left-5 top-0 h-full w-px bg-gradient-to-b from-brand-400 to-vital-400" />

          <div className="space-y-12">
            {STEPS.map((step, i) => (
              <div key={step.title} className="workflow-step relative">
                <div className="absolute -left-14 flex h-10 w-10 items-center justify-center rounded-full border border-brand-400/40 bg-ink-900 text-brand-300">
                  <step.icon size={17} />
                </div>
                <p className="text-xs font-semibold text-brand-400">Step {i + 1}</p>
                <h3 className="mt-1 font-display text-lg font-semibold text-white">{step.title}</h3>
                <p className="mt-1.5 max-w-lg text-sm leading-relaxed text-ink-400">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
