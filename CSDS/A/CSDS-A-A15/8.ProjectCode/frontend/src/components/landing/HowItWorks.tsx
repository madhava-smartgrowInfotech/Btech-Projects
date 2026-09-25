import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { FileCheck2, ScanLine, UploadCloud, Wand2 } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'

gsap.registerPlugin(ScrollTrigger)

const STEPS = [
  {
    icon: UploadCloud,
    title: 'Upload the surface image',
    description: 'Drop in a photo from a line camera, handheld scanner, or phone — JPG, PNG or WEBP.',
  },
  {
    icon: ScanLine,
    title: 'Model scans for defects',
    description: 'The trained classifier scores six defect categories and localizes the affected region.',
  },
  {
    icon: Wand2,
    title: 'Explanation is generated',
    description: 'A Grad-CAM heatmap and a plain-language root-cause narrative are produced automatically.',
  },
  {
    icon: FileCheck2,
    title: 'Report is ready to act on',
    description: 'Severity, causes and corrective actions are compiled into a downloadable PDF instantly.',
  },
]

export function HowItWorks() {
  const sectionRef = useRef<HTMLElement>(null)
  const lineRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!sectionRef.current || !lineRef.current) return
    const ctx = gsap.context(() => {
      gsap.fromTo(
        lineRef.current,
        { scaleX: 0 },
        {
          scaleX: 1,
          ease: 'none',
          transformOrigin: 'left center',
          scrollTrigger: {
            trigger: sectionRef.current,
            start: 'top 70%',
            end: 'bottom 60%',
            scrub: 0.5,
          },
        },
      )
    }, sectionRef)
    return () => ctx.revert()
  }, [])

  return (
    <section ref={sectionRef} id="how-it-works" className="relative py-28 border-t border-white/5">
      <div className="mx-auto max-w-7xl px-6">
        <div className="max-w-2xl mb-16">
          <p className="text-sm font-medium text-violet-400 mb-3">How it works</p>
          <h2 className="font-display text-4xl font-bold text-white">
            From raw image to actionable insight in under a second.
          </h2>
        </div>

        <div className="relative grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="hidden md:block absolute top-6 left-[12.5%] right-[12.5%] h-px bg-white/10" />
          <div
            ref={lineRef}
            className="hidden md:block absolute top-6 left-[12.5%] right-[12.5%] h-px bg-gradient-to-r from-cyan-400 via-violet-400 to-rose-400"
          />
          {STEPS.map((step, i) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.5, delay: i * 0.12 }}
              className="relative"
            >
              <div className="relative z-10 h-12 w-12 rounded-full bg-[#0b0f19] border border-white/10 flex items-center justify-center mb-5">
                <step.icon className="h-5 w-5 text-cyan-300" />
              </div>
              <p className="text-xs font-mono text-slate-500 mb-1">STEP {i + 1}</p>
              <h3 className="font-display text-base font-semibold text-white mb-2">{step.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{step.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
