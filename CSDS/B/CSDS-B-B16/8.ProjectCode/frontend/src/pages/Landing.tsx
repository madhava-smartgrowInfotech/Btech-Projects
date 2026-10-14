import { Activity, Eye, FileText, Flame, HeartPulse, Layers, LineChart, ScanEye, type LucideIcon } from "lucide-react";
import { Link } from "react-router";

import { ThemeToggle } from "@/components/app/ThemeToggle";
import { Disclaimer } from "@/components/app/Disclaimer";
import { Logo } from "@/components/brand/Logo";
import { ExamplePipeline } from "@/components/landing/ExamplePipeline";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { StatsStrip } from "@/components/landing/StatsStrip";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { FadeIn } from "@/components/motion/FadeIn";
import { Marquee } from "@/components/motion/Marquee";
import { SlideUp } from "@/components/motion/SlideUp";
import { SmoothScroll } from "@/components/motion/SmoothScroll";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useAuth } from "@/lib/auth";

const FEATURES: [LucideIcon, string, string][] = [
  [ScanEye, "Fundus preprocessing", "Green channel, CLAHE enhancement, resizing and normalisation shown step by step, with a blur and illumination quality check."],
  [Layers, "Haar wavelet features", "A 2-level Haar transform splits the image into LL, LH, HL and HH sub-bands that highlight vessels and lesions."],
  [Eye, "Retinopathy detection", "A compact LeNet CNN reads the wavelet sub-bands and returns a hypertensive retinopathy probability."],
  [Flame, "Explainable results", "Grad-CAM heatmaps show where the model looked; a Frangi filter maps the retinal vessels."],
  [HeartPulse, "Heart-disease risk", "A Random Forest scores the clinical profile and SHAP lists the factors that drive the risk."],
  [Activity, "Combined risk stage", "Retinal and clinical results merge into Low, Moderate, High or Very high with recommendations."],
  [FileText, "Screening report", "A PDF with the images, findings, risk stage and recommendations, ready to file or share."],
  [LineChart, "Measured performance", "Accuracy, sensitivity, specificity, F1, ROC-AUC and confusion matrices for both models."],
];

const CHIPS = ["Fundus preprocessing", "Haar wavelets", "LeNet CNN", "Grad-CAM", "Random Forest", "SHAP", "PDF report"];

export default function Landing() {
  const { signedIn } = useAuth();
  const appHref = signedIn ? "/screening/new" : "/login";

  return (
    <div className="min-h-dvh">
      <SmoothScroll />
      <AuroraBackground />
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-popover focus:px-3 focus:py-2">
        Skip to content
      </a>

      <header className="sticky top-0 z-30 px-3 pt-3">
        <div className="glass mx-auto flex h-14 max-w-6xl items-center gap-2 rounded-2xl px-3 sm:px-4">
          <Link to="/" aria-label="RetinaGuard home">
            <Logo />
          </Link>
          <div className="ml-auto flex items-center gap-1">
            <Button variant="ghost" size="sm" asChild className="hidden sm:inline-flex">
              <a href="#how-it-works">How it works</a>
            </Button>
            <ThemeToggle />
            <Button size="sm" asChild>
              <Link to={appHref}>{signedIn ? "Open app" : "Sign in"}</Link>
            </Button>
          </div>
        </div>
      </header>

      <main id="main">
        <section className="mx-auto grid max-w-6xl items-center gap-12 overflow-x-clip px-4 pb-16 pt-14 sm:px-6 lg:grid-cols-[1.1fr_1fr] lg:pb-24 lg:pt-24">
          <div className="space-y-6">
            <FadeIn>
              <p className="inline-flex items-center gap-2 rounded-full border border-[var(--glass-border)] bg-[var(--glass)] px-3 py-1 text-xs font-medium text-violet-ink">
                <span className="size-1.5 rounded-full bg-success" aria-hidden /> Retinal and cardiovascular screening
              </p>
            </FadeIn>
            <SlideUp>
              <h1 className="font-display text-4xl font-semibold leading-[1.05] tracking-tight text-balance sm:text-5xl lg:text-6xl">
                Catch hypertensive retinopathy and heart risk in <span className="text-gradient">one screening</span>.
              </h1>
            </SlideUp>
            <FadeIn delay={0.15}>
              <p className="max-w-xl text-base text-muted-foreground sm:text-lg">
                RetinaGuard analyses a fundus photograph with wavelet features and a CNN, scores the patient's clinical profile, and combines
                both into one explained risk stage for ophthalmologists, physicians and screening camps.
              </p>
            </FadeIn>
            <FadeIn delay={0.25} className="flex flex-wrap gap-3">
              <Button size="lg" asChild>
                <Link to={appHref}>Start a screening</Link>
              </Button>
              <Button size="lg" variant="secondary" asChild>
                <a href="#how-it-works">See how it works</a>
              </Button>
            </FadeIn>
          </div>
          <FadeIn delay={0.2}>
            <ExamplePipeline />
          </FadeIn>
        </section>

        <section aria-label="Pipeline components" className="py-4">
          <Marquee speed={38}>
            {CHIPS.map((chip) => (
              <span key={chip} className="glass whitespace-nowrap rounded-full px-4 py-2 text-sm text-muted-foreground">
                {chip}
              </span>
            ))}
          </Marquee>
        </section>

        <div className="space-y-24 py-16">
          <StatsStrip />
          <HowItWorks />

          <section id="features" className="mx-auto max-w-6xl scroll-mt-24 px-4 sm:px-6">
            <SlideUp className="mb-10 max-w-2xl space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">What is inside</p>
              <h2 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">Everything for one screening, in one place</h2>
            </SlideUp>
            <Stagger inView className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" gap={0.07}>
              {FEATURES.map(([Icon, title, text]) => (
                <StaggerItem key={title} className="h-full">
                  <Card interactive className="h-full p-5">
                    <span className="mb-4 grid size-10 place-items-center rounded-xl bg-grad-soft text-violet-ink ring-1 ring-[var(--glass-border)] [&_svg]:size-5">
                      <Icon aria-hidden />
                    </span>
                    <h3 className="mb-1 font-display font-semibold">{title}</h3>
                    <p className="text-sm text-muted-foreground">{text}</p>
                  </Card>
                </StaggerItem>
              ))}
            </Stagger>
          </section>

          <section className="mx-auto max-w-3xl px-4 sm:px-6">
            <Disclaimer />
          </section>

          <section className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="glass-strong relative overflow-hidden rounded-3xl p-8 text-center sm:p-12">
              <div aria-hidden className="absolute inset-0 bg-grad-soft opacity-60" />
              <h2 className="relative font-display text-2xl font-semibold sm:text-3xl">Ready to screen a patient?</h2>
              <p className="relative mx-auto mt-2 max-w-xl text-muted-foreground">
                Each result is saved to the patient's history and can be exported as a PDF report.
              </p>
              <div className="relative mt-6 flex justify-center">
                <Button size="lg" asChild>
                  <Link to={appHref}>{signedIn ? "Open the app" : "Sign in to start"}</Link>
                </Button>
              </div>
            </div>
          </section>
        </div>
      </main>

      <footer className="border-t border-[var(--glass-border)] px-4 py-8 text-center text-xs text-muted-foreground">
        RetinaGuard · clinical decision support for retinal and cardiovascular screening
      </footer>
    </div>
  );
}
