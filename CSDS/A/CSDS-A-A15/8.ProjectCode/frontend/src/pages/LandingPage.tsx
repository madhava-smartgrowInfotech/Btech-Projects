import { CTASection } from '@/components/landing/CTASection'
import { DefectMarquee } from '@/components/landing/DefectMarquee'
import { FeatureGrid } from '@/components/landing/FeatureGrid'
import { Hero } from '@/components/landing/Hero'
import { HowItWorks } from '@/components/landing/HowItWorks'
import { StatsSection } from '@/components/landing/StatsSection'
import { Footer } from '@/components/layout/Footer'
import { Navbar } from '@/components/layout/Navbar'
import { useLenis } from '@/hooks/useLenis'

export function LandingPage() {
  useLenis()

  return (
    <div className="bg-[#05070c]">
      <Navbar />
      <Hero />
      <DefectMarquee />
      <FeatureGrid />
      <HowItWorks />
      <StatsSection />
      <CTASection />
      <Footer />
    </div>
  )
}
