import { ArrowRight, BookOpenText, Camera, FlaskConical, Sparkles, Store, Tractor, Microscope } from "lucide-react";
import { Link } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { KnowledgeCard } from "@/components/landing/KnowledgeCard";
import { StatsStrip } from "@/components/landing/StatsStrip";
import { Marquee } from "@/components/motion/Marquee";
import { Reveal } from "@/components/motion/Reveal";
import { SlideUp } from "@/components/motion/SlideUp";
import { SmoothScroll } from "@/components/motion/SmoothScroll";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { LanguageMenu } from "@/components/ui/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { useDiseases } from "@/lib/queries";

const PERSONAS = [
  { icon: Tractor, title: "Farmers", text: "Spot a problem early, get the spray dose and cost, and keep a record of every field visit." },
  { icon: Microscope, title: "Extension officers", text: "Check what a farmer saw, export the report as PDF and watch which diagnoses keep recurring." },
  { icon: Store, title: "Agro dealers", text: "Recommend the right treatment type with a written report the farmer can keep." },
];

const FEATURES = [
  { icon: Camera, title: "Leaf photo to diagnosis", text: "Upload or capture a leaf and get the top-3 candidates with confidence and severity." },
  { icon: FlaskConical, title: "Chemical, organic, cultural", text: "Every diagnosis comes with three kinds of treatment, typical costs and prevention steps." },
  { icon: BookOpenText, title: "Searchable disease guide", text: "Browse all 38 classes by crop or symptom, without needing an account." },
];

export default function Landing() {
  const { user } = useAuth();
  const { t } = useLang();
  const diseases = useDiseases();
  const crops = [...new Set((diseases.data ?? []).map((d) => d.crop))].sort();

  return (
    <div className="relative overflow-x-clip">
      <SmoothScroll />
      <AuroraBackground />
      <a href="#top" className="sr-only z-[90] rounded-lg bg-popover px-3 py-2 focus:not-sr-only focus:fixed focus:left-3 focus:top-3">
        Skip to content
      </a>

      <header className="sticky top-0 z-40 px-3 pt-3">
        <div className="glass mx-auto flex h-14 max-w-6xl items-center gap-2 rounded-2xl px-3 sm:px-4">
          <Link to="/" aria-label="AgriVision home">
            <Logo />
          </Link>
          <nav aria-label="Page sections" className="ml-6 hidden items-center gap-1 text-sm md:flex">
            <a href="#how-it-works" className="rounded-lg px-3 py-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground">
              How it works
            </a>
            <a href="#features" className="rounded-lg px-3 py-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground">
              Features
            </a>
            <Link to="/encyclopedia" className="rounded-lg px-3 py-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground">
              {t("nav.guide", "Disease guide")}
            </Link>
          </nav>
          <div className="ml-auto flex items-center gap-1">
            <LanguageMenu />
            <ThemeToggle />
            {user ? (
              <Button asChild size="sm">
                <Link to="/dashboard">
                  {t("nav.dashboard", "Dashboard")} <ArrowRight />
                </Link>
              </Button>
            ) : (
              <>
                <Button asChild size="sm" variant="ghost" className="hidden sm:inline-flex">
                  <Link to="/login">{t("common.signin", "Sign in")}</Link>
                </Button>
                <Button asChild size="sm">
                  <Link to="/register">{t("common.getStarted", "Get started")}</Link>
                </Button>
              </>
            )}
          </div>
        </div>
      </header>

      <main id="top">
        <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-16 pt-16 sm:px-6 sm:pt-24 lg:grid-cols-[1.1fr_1fr] lg:gap-8 lg:pb-24">
          <div className="space-y-6">
            <SlideUp>
              <Badge tone="violet" className="gap-1.5 px-3 py-1 text-xs">
                <Sparkles aria-hidden />
                {diseases.data ? `${diseases.data.length} classes · ${crops.length} crops · treatment plans` : "Crop disease detection and advice"}
              </Badge>
            </SlideUp>
            <SlideUp delay={0.08}>
              <h1 className="font-display text-4xl font-semibold leading-[1.05] tracking-tight text-balance sm:text-5xl lg:text-6xl">
                {t("hero.a", "Detect crop disease in")} <span className="text-gradient">{t("hero.b", "seconds, not days.")}</span>
              </h1>
            </SlideUp>
            <SlideUp delay={0.16}>
              <p className="max-w-xl text-lg text-muted-foreground">
                Snap a leaf photo. AgriVision names the likely disease, scores its confidence and prescribes organic and chemical treatment, built for farmers,
                extension officers and agro dealers.
              </p>
            </SlideUp>
            <SlideUp delay={0.24} className="flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link to={user ? "/detect" : "/register"}>
                  {t("hero.cta", "Start detecting, free")} <ArrowRight />
                </Link>
              </Button>
              <Button asChild size="lg" variant="secondary">
                <Link to="/encyclopedia">
                  <BookOpenText /> {t("hero.guide", "Disease guide")}
                </Link>
              </Button>
            </SlideUp>
          </div>
          <SlideUp delay={0.3}>
            <KnowledgeCard />
          </SlideUp>
        </section>

        {crops.length > 0 && (
          <div className="border-y border-[var(--glass-border)] bg-[var(--glass)] py-4 backdrop-blur-sm">
            <Marquee>
              {crops.map((c) => (
                <span key={c} className="mx-5 inline-flex items-center gap-2 text-sm text-muted-foreground">
                  <span className="size-1.5 rounded-full bg-grad-primary" aria-hidden /> {c}
                </span>
              ))}
            </Marquee>
          </div>
        )}

        <div className="py-16 sm:py-24">
          <StatsStrip />
        </div>

        <HowItWorks />

        <section id="features" className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
          <Reveal className="mb-10 space-y-3 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">What you can do</p>
            <h2 className="font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
              Built for the field, <span className="text-gradient">useful at the desk</span>
            </h2>
          </Reveal>
          <Stagger inView className="grid gap-4 md:grid-cols-3">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <StaggerItem key={title}>
                <Card interactive className="h-full space-y-3 p-6">
                  <span className="grid size-11 place-items-center rounded-2xl bg-grad-primary text-white shadow-[0_10px_30px_-10px_rgba(34,160,107,0.8)]">
                    <Icon className="size-5" />
                  </span>
                  <h3 className="font-display text-lg font-semibold">{title}</h3>
                  <p className="text-muted-foreground">{text}</p>
                </Card>
              </StaggerItem>
            ))}
          </Stagger>
          <Stagger inView className="mt-4 grid gap-4 md:grid-cols-3">
            {PERSONAS.map(({ icon: Icon, title, text }) => (
              <StaggerItem key={title}>
                <Card className="h-full space-y-2 p-6">
                  <div className="flex items-center gap-2">
                    <Icon className="size-5 text-violet-ink" aria-hidden />
                    <h3 className="font-display font-semibold">{title}</h3>
                  </div>
                  <p className="text-sm text-muted-foreground">{text}</p>
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
                Ready to protect <span className="text-gradient">your crop?</span>
              </h2>
              <p className="relative mx-auto mt-3 max-w-lg text-muted-foreground">Free for smallholder farmers. Create an account in about thirty seconds, or try the demo farmer.</p>
              <div className="relative mt-6 flex flex-wrap justify-center gap-3">
                <Button asChild size="lg">
                  <Link to={user ? "/detect" : "/register"}>
                    {user ? "Scan a leaf" : "Create free account"} <ArrowRight />
                  </Link>
                </Button>
                {!user && (
                  <Button asChild size="lg" variant="secondary">
                    <Link to="/login">{t("common.signin", "Sign in")}</Link>
                  </Button>
                )}
              </div>
            </div>
          </Reveal>
        </section>
      </main>

      <footer className="border-t border-[var(--glass-border)] px-4 py-8 text-center text-sm text-muted-foreground">
        <p>AgriVision · AI-powered crop disease detection and recommendation · results are advice, not a laboratory diagnosis.</p>
        <p className="mt-2 text-xs">
          Demo login: <b className="text-foreground">demo@agrivision.ai</b> / <b className="text-foreground">demo1234</b> ·{" "}
          <a className="underline underline-offset-2 hover:text-foreground" href="/api/v1/diseases" target="_blank" rel="noreferrer">
            API
          </a>{" "}
          ·{" "}
          <a className="underline underline-offset-2 hover:text-foreground" href="/api/health" target="_blank" rel="noreferrer">
            Health
          </a>
        </p>
      </footer>
    </div>
  );
}
