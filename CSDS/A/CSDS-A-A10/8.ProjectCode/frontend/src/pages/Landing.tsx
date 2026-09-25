import { Footer } from '@/components/landing/Footer'
import { Hero } from '@/components/landing/Hero'
import { Intelligence } from '@/components/landing/Intelligence'
import { Navbar } from '@/components/landing/Navbar'
import { Platform } from '@/components/landing/Platform'
import { Results } from '@/components/landing/Results'
import { SmoothScroll } from '@/components/landing/SmoothScroll'
import { Workflow } from '@/components/landing/Workflow'

export default function Landing() {
  return (
    <SmoothScroll>
      <div className="min-h-screen bg-ink-950">
        <Navbar />
        <Hero />
        <Platform />
        <Workflow />
        <Intelligence />
        <Results />
        <Footer />
      </div>
    </SmoothScroll>
  )
}
