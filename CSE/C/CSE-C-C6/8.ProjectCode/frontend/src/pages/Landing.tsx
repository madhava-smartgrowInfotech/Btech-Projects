import { ArrowRight, BarChart3, ShieldCheck, Sparkles, Zap } from "lucide-react";
import { Link } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { LiveVerdict } from "@/components/landing/LiveVerdict";
import { StatsStrip } from "@/components/landing/StatsStrip";
import { Marquee } from "@/components/motion/Marquee";
import { Reveal } from "@/components/motion/Reveal";
import { SmoothScroll } from "@/components/motion/SmoothScroll";
import { SlideUp } from "@/components/motion/SlideUp";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

const FEATURES = [
  {
    icon: ShieldCheck,
    title: "Three honest verdicts",
    text: "REAL, PARTIALLY TRUE or FAKE. The middle class catches articles that blend verified facts with exaggerated claims.",
  },
  {
    icon: Zap,
    title: "Explained, not just labelled",
    text: "Every result shows its confidence, the probability of each class and the sensational or credibility cue words it noticed.",
  },
  {
    icon: BarChart3,
    title: "Screen a whole CSV",
    text: "Upload a file of articles, get a verdict for each row, see the distribution and download the results.",
  },
  {
    icon: Sparkles,
    title: "Retrain on your data",
    text: "Bring your own labelled CSV and tune the Firefly search. The new model takes over without restarting anything.",
  },
];

const TECH = ["TF-IDF", "25 stylometric signals", "PCA 95% variance", "Firefly algorithm", "RBF SVM", "One-vs-rest", "Balanced class weights", "Cross-validated macro-F1"];

export default function Landing() {
  return (
    <div className="relative overflow-x-clip">
      <SmoothScroll />
      <AuroraBackground />
      <a href="#top" className="sr-only z-[90] rounded-lg bg-popover px-3 py-2 focus:not-sr-only focus:fixed focus:left-3 focus:top-3">
        Skip to content
      </a>

      <header className="sticky top-0 z-40 px-3 pt-3">
        <div className="glass mx-auto flex h-14 max-w-6xl items-center gap-2 rounded-2xl px-3 sm:px-4">
          <Link to="/" aria-label="TruthGlow home">
            <Logo />
          </Link>
          <nav aria-label="Page sections" className="ml-6 hidden items-center gap-1 text-sm md:flex">
            <a href="#how-it-works" className="rounded-lg px-3 py-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground">
              How it works
            </a>
            <a href="#features" className="rounded-lg px-3 py-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground">
              Features
            </a>
          </nav>
          <div className="ml-auto flex items-center gap-1">
            <ThemeToggle />
            <Button asChild size="sm">
              <Link to="/app">
                Open the app <ArrowRight />
              </Link>
            </Button>
          </div>
        </div>
      </header>

      <main id="top">
        <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-16 pt-16 sm:px-6 sm:pt-24 lg:grid-cols-[1.1fr_1fr] lg:gap-8 lg:pb-24">
          <div className="space-y-6">
            <SlideUp>
              <Badge tone="violet" className="gap-1.5 px-3 py-1 text-xs">
                <Sparkles aria-hidden /> PCA + Firefly + MSVM
              </Badge>
            </SlideUp>
            <SlideUp delay={0.08}>
              <h1 className="font-display text-4xl font-semibold leading-[1.05] tracking-tight text-balance sm:text-5xl lg:text-6xl">
                Spot fake news <span className="text-gradient">before you share it</span>
              </h1>
            </SlideUp>
            <SlideUp delay={0.16}>
              <p className="max-w-xl text-lg text-muted-foreground">
                Paste an article and get a REAL, PARTIALLY TRUE or FAKE verdict from a feature-optimised multi-class SVM, with the confidence behind it and
                the cue words that shaped it.
              </p>
            </SlideUp>
            <SlideUp delay={0.24} className="flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link to="/app">
                  Try the detector <ArrowRight />
                </Link>
              </Button>
              <Button asChild size="lg" variant="secondary">
                <Link to="/app/analytics">
                  <BarChart3 /> See model analytics
                </Link>
              </Button>
            </SlideUp>
          </div>
          <SlideUp delay={0.3}>
            <LiveVerdict />
          </SlideUp>
        </section>

        <div className="border-y border-[var(--glass-border)] bg-[var(--glass)] py-4 backdrop-blur-sm">
          <Marquee>
            {TECH.map((t) => (
              <span key={t} className="mx-5 inline-flex items-center gap-2 text-sm text-muted-foreground">
                <span className="size-1.5 rounded-full bg-grad-primary" aria-hidden /> {t}
              </span>
            ))}
          </Marquee>
        </div>

        <div className="py-16 sm:py-24">
          <StatsStrip />
        </div>

        <HowItWorks />

        <section id="features" className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
          <Reveal className="mb-10 space-y-3 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">What you can do</p>
            <h2 className="font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
              One model, <span className="text-gradient">four ways to use it</span>
            </h2>
          </Reveal>
          <Stagger inView className="grid gap-4 sm:grid-cols-2">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <StaggerItem key={title}>
                <Card interactive className="h-full space-y-3 p-6">
                  <span className="grid size-11 place-items-center rounded-2xl bg-grad-primary text-white shadow-[0_10px_30px_-10px_rgba(124,92,255,0.8)]">
                    <Icon className="size-5" />
                  </span>
                  <h3 className="font-display text-lg font-semibold">{title}</h3>
                  <p className="text-muted-foreground">{text}</p>
                </Card>
              </StaggerItem>
            ))}
          </Stagger>
        </section>

        <section className="mx-auto max-w-4xl px-4 pb-24 sm:px-6">
          <Reveal>
            <div className="glass-strong relative overflow-hidden rounded-3xl px-6 py-12 text-center sm:px-12">
              <div aria-hidden className="absolute -top-20 left-1/2 h-40 w-3/4 -translate-x-1/2 rounded-full bg-grad-primary opacity-30 blur-3xl" />
              <h2 className="relative font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
                Check an article <span className="text-gradient">in seconds</span>
              </h2>
              <p className="relative mx-auto mt-3 max-w-lg text-muted-foreground">
                Everything runs on your own computer. Nothing you paste is sent anywhere else.
              </p>
              <div className="relative mt-6 flex justify-center">
                <Button asChild size="lg">
                  <Link to="/app">
                    Open the detector <ArrowRight />
                  </Link>
                </Button>
              </div>
            </div>
          </Reveal>
        </section>
      </main>

      <footer className="border-t border-[var(--glass-border)] px-4 py-8 text-center text-sm text-muted-foreground">
        TruthGlow · Fake News Detection System Using Feature-Based Optimised MSVM Classification · a screening aid, not a fact-checker.
      </footer>
    </div>
  );
}
