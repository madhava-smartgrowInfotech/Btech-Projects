import { useLenis } from '../hooks/useLenis'
import { Navbar } from '../components/layout/Navbar'
import { Footer } from '../components/layout/Footer'
import { Hero } from '../components/landing/Hero'
import { FeatureGrid } from '../components/landing/FeatureGrid'
import { HowItWorks } from '../components/landing/HowItWorks'
import { StatsStrip } from '../components/landing/StatsStrip'
import { CTASection } from '../components/landing/CTASection'

export function Landing() {
  useLenis()

  return (
    <div className="relative">
      <Navbar />
      <Hero />
      <FeatureGrid />
      <HowItWorks />
      <StatsStrip />
      <CTASection />
      <Footer />
    </div>
  )
}
