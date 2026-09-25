import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { Button } from '../ui/Button'
import { Reveal } from '../ui/Reveal'

export function CTASection() {
  return (
    <section className="relative py-28 px-6">
      <div className="mx-auto max-w-4xl">
        <Reveal>
          <div className="glass glow-card rounded-3xl px-8 py-16 sm:px-16 text-center relative overflow-hidden">
            <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-96 h-96 rounded-full bg-emerald-500/15 blur-3xl -z-10" />
            <h2 className="font-display text-3xl sm:text-4xl font-bold max-w-xl mx-auto">
              Start scoring your next seed batch today
            </h2>
            <p className="text-[var(--color-text-muted)] mt-4 max-w-md mx-auto">
              Upload an image, enter field conditions, and get a confidence-scored, explained
              prediction in under three seconds.
            </p>
            <div className="mt-9 flex justify-center">
              <Link to="/app">
                <Button size="lg" icon={<ArrowRight size={17} />}>
                  Open workspace
                </Button>
              </Link>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  )
}
