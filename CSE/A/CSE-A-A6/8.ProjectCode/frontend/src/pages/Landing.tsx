import { Activity, ArrowRight, Cpu, FlaskConical, History, ShieldAlert, SlidersHorizontal } from "lucide-react";
import { Link } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { ScriptedPreview } from "@/components/landing/ScriptedPreview";
import { StatsStrip } from "@/components/landing/StatsStrip";
import { FadeIn, Marquee, Reveal, SlideUp, SmoothScroll } from "@/components/motion";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { ThemeToggle } from "@/components/ui/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/lib/auth";
import { useAbout, useConfig } from "@/lib/queries";

const FEATURES = [
  { icon: Activity, title: "Live monitor", text: "Camera or scripted simulation, a clear verdict, the reason behind it and every measurement.", to: "/app" },
  { icon: History, title: "Event history", text: "UTC-stamped numeric events, an EAR chart for live versus simulation, and one-click CSV export.", to: "/app/history" },
  { icon: SlidersHorizontal, title: "Thresholds", text: "Six validated rule values, with personal calibration that sets your own closed-eye threshold.", to: "/app/thresholds" },
  { icon: FlaskConical, title: "Research", text: "Subject-separated offline evaluation of a consented, labelled dataset. Never used for live warnings.", to: "/app/research" },
];

export default function Landing() {
  const { user } = useAuth();
  const config = useConfig();
  const about = useAbout();
  const cta = user ? "/app" : "/login";
  return (
    <div className="min-h-dvh overflow-x-clip">
      <SmoothScroll />
      <AuroraBackground />
      <a href="#top" className="sr-only z-[90] rounded-lg bg-popover px-3 py-2 focus:not-sr-only focus:fixed focus:left-3 focus:top-3">
        Skip to content
      </a>

      <header className="sticky top-0 z-40 px-3 pt-3">
        <div className="glass mx-auto flex h-14 max-w-6xl items-center gap-2 rounded-2xl px-3 sm:px-4">
          <Link to="/" aria-label="Smart Rider home">
            <Logo />
          </Link>
          <nav aria-label="Page sections" className="ml-6 hidden items-center gap-1 md:flex">
            <a href="#how-it-works" className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground">
              How it works
            </a>
            <a href="#features" className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground">
              Features
            </a>
            <a href="#limits" className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground">
              Limits
            </a>
          </nav>
          <div className="ml-auto flex items-center gap-1">
            <ThemeToggle />
            <Button asChild size="sm">
              <Link to={cta}>{user ? "Open app" : "Sign in"}</Link>
            </Button>
          </div>
        </div>
      </header>

      <main id="top">
        <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-16 pt-14 sm:px-6 lg:grid-cols-[1.1fr_1fr] lg:pb-24 lg:pt-20">
          <div className="space-y-6">
            <FadeIn>
              <Badge tone="violet" className="px-3 py-1 text-xs">
                Two-wheeler rider safety · stationary demonstration
              </Badge>
            </FadeIn>
            <SlideUp delay={0.05}>
              <h1 className="font-display text-4xl font-bold leading-[1.05] tracking-tight text-balance sm:text-5xl lg:text-6xl">
                A second pair of eyes on <span className="text-gradient">rider alertness.</span>
              </h1>
            </SlideUp>
            <SlideUp delay={0.12}>
              <p className="max-w-xl text-lg text-muted-foreground">
                Smart Rider reads visible eye and head cues from your webcam and warns of <strong className="font-semibold text-foreground">possible drowsiness or impairment</strong> with
                rules you can inspect. It cannot confirm alcohol use, and it never touches ignition or brakes.
              </p>
            </SlideUp>
            <SlideUp delay={0.2} className="flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link to={cta}>
                  Open the monitor <ArrowRight />
                </Link>
              </Button>
              <Button asChild size="lg" variant="secondary">
                <a href="#how-it-works">See how it works</a>
              </Button>
            </SlideUp>
          </div>
          <FadeIn delay={0.15}>
            <ScriptedPreview />
          </FadeIn>
        </section>

        <section aria-label="Scenarios you can simulate" className="pb-16">
          <Marquee speed={60}>
            {(config.data?.scenarios ?? ["Normal", "Prolonged eye closure", "Missing face", "Poor lighting"]).map((s) => (
              <span key={s} className="glass flex h-14 items-center gap-2 rounded-2xl px-6 font-display text-lg font-semibold text-gradient">
                <Cpu className="size-4 text-violet-ink" /> {s}
              </span>
            ))}
            {["Normal", "Possible impairment or drowsiness", "Unable to assess"].map((s) => (
              <span key={s} className="glass grid h-14 place-items-center rounded-2xl px-6 font-display text-base font-semibold text-muted-foreground">
                {s}
              </span>
            ))}
          </Marquee>
        </section>

        <StatsStrip />

        <HowItWorks />

        <section id="features" className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <div className="mb-10 space-y-3 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Everything in one place</p>
            <h2 className="font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
              Monitor, review, tune, <span className="text-gradient">evaluate</span>
            </h2>
          </div>
          <Reveal className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map(({ icon: Icon, title, text, to }) => (
              <Link key={title} to={user ? to : "/login"} data-reveal className="glass sweep group flex flex-col gap-3 rounded-3xl p-5 transition-transform duration-300 hover:-translate-y-1">
                <span className="grid size-11 place-items-center rounded-2xl bg-grad-primary text-white shadow-[0_10px_24px_-10px_rgba(124,92,255,0.9)]">
                  <Icon className="size-5" />
                </span>
                <h3 className="font-display text-lg font-semibold">{title}</h3>
                <p className="text-sm text-muted-foreground">{text}</p>
                <span className="mt-auto inline-flex items-center gap-1 text-sm font-medium text-violet-ink">
                  Open <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
                </span>
              </Link>
            ))}
          </Reveal>
        </section>

        <section id="limits" className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
          <div className="glass relative overflow-hidden rounded-3xl p-6 sm:p-8">
            <div aria-hidden className="absolute -left-10 -top-10 size-44 rounded-full bg-warning/20 blur-3xl" />
            <div className="relative flex items-start gap-4">
              <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-warning/15 text-warning">
                <ShieldAlert className="size-5" />
              </span>
              <div className="space-y-3">
                <h2 className="font-display text-xl font-semibold sm:text-2xl">Read this before you trust a screen</h2>
                <ul className="grid gap-x-8 gap-y-2 text-sm text-muted-foreground md:grid-cols-2">
                  {(config.data?.disclaimers ?? []).map((d) => (
                    <li key={d} className="flex gap-2">
                      <span aria-hidden className="mt-2 size-1.5 shrink-0 rounded-full bg-warning" />
                      {d}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="mx-auto max-w-6xl px-4 pb-10 sm:px-6">
        <div className="glass flex flex-col gap-3 rounded-3xl p-5 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <Logo />
          <p className="max-w-xl sm:text-right">
            {about.data ? (
              <>Inspired by Feng and Li (2026), IEEE Access 14. This project borrows only the idea of fusing observable signals with personal calibration.</>
            ) : (
              "CSE-A · Batch 6 · Smart Rider Impairment Warning System for Two-Wheelers"
            )}
          </p>
        </div>
      </footer>
    </div>
  );
}
