import { ArrowRight, BarChart3, Brain, Clock, Languages, MapPinned, MessageSquareText, ShieldCheck } from "lucide-react";
import { Link } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { StatsStrip } from "@/components/landing/StatsStrip";
import { Marquee } from "@/components/motion/Marquee";
import { Reveal } from "@/components/motion/Reveal";
import { SlideUp } from "@/components/motion/SlideUp";
import { SmoothScroll } from "@/components/motion/SmoothScroll";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ThemeToggle } from "@/components/ui/AppShell";
import { homeFor, useAuth } from "@/lib/auth";
import { useMeta } from "@/lib/queries";

const FEATURES = [
  { icon: Languages, title: "Understands English, Hindi and Hinglish", text: "Citizens write the way they speak. Complaints are classified by category and routed to the right department automatically." },
  { icon: Clock, title: "Priority and resolution time", text: "Every complaint gets a Low to Critical priority and an expected resolution time learned from real service-request history, with an SLA-breach warning." },
  { icon: Brain, title: "Explains every suggestion", text: "Officers see the words that drove the category and the factors behind priority and time - no black boxes." },
  { icon: ShieldCheck, title: "Officers stay in control", text: "Accept or override each suggestion with a reason. Overrides become training labels and the model retrains in one click." },
  { icon: BarChart3, title: "Hotspots and SLA analytics", text: "See recurring issues by ward, SLA compliance by department and category trends as they happen." },
  { icon: MessageSquareText, title: "Replies in the citizen's language", text: "A status reply is drafted in the language the citizen used, ready for the officer to edit and send." },
];

// the same example complaints the filing form offers
const EXAMPLES = [
  { lang: "Hindi", text: "हमारे मोहल्ले में पिछले 5 दिन से पानी की सप्लाई बंद है, बच्चे और बुजुर्ग बहुत परेशान हैं।", hi: true },
  { lang: "Hinglish", text: "Main road par bahut bada gaddha hai, kal raat ek bike wala gir gaya. Jaldi theek karwaiye." },
  { lang: "English", text: "Garbage has not been collected from our lane for a week and it is starting to smell." },
];

export default function Landing() {
  const { user } = useAuth();
  const meta = useMeta();
  const cta = user ? homeFor(user) : "/login";

  return (
    <div className="relative min-h-dvh">
      <SmoothScroll />
      <AuroraBackground />

      <header className="sticky top-0 z-30 px-3 pt-3">
        <div className="glass mx-auto flex h-14 max-w-6xl items-center justify-between rounded-2xl px-3 sm:px-4">
          <Link to="/" aria-label="CivicPulse home">
            <Logo />
          </Link>
          <div className="flex items-center gap-1.5">
            <ThemeToggle />
            <Button asChild variant="secondary" size="sm" magnetic={false}>
              <Link to={cta}>{user ? "Open dashboard" : "Log in"}</Link>
            </Button>
          </div>
        </div>
      </header>

      <main id="main">
        <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-16 pt-14 sm:px-6 md:pt-20 lg:grid-cols-[1.15fr_1fr] lg:gap-10 lg:pb-24">
          <SlideUp className="space-y-6">
            <Badge tone="violet" className="px-3 py-1 text-xs">
              Decision support for grievance offices
            </Badge>
            <h1 className="font-display text-4xl font-bold leading-[1.08] tracking-tight text-balance sm:text-5xl lg:text-6xl">
              Every citizen complaint <span className="text-gradient">understood, prioritised and routed</span> - with the reasons shown.
            </h1>
            <p className="max-w-xl text-base text-muted-foreground sm:text-lg">
              CivicPulse reads complaints in English, Hindi and Hinglish, predicts priority and resolution time, recommends the responsible department
              and explains each suggestion. Officers make the final call.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link to={user?.role === "citizen" ? "/app/file" : "/login"}>
                  File a complaint <ArrowRight />
                </Link>
              </Button>
              <Button asChild size="lg" variant="secondary" magnetic={false}>
                <Link to={user && user.role !== "citizen" ? "/app/queue" : "/login"}>Officer workbench</Link>
              </Button>
            </div>
          </SlideUp>

          <div className="relative mx-auto w-full max-w-md lg:max-w-none">
            <div aria-hidden className="absolute -inset-6 rounded-[2.5rem] bg-grad-primary opacity-20 blur-3xl" />
            <Card strong className="relative space-y-3 p-4 sm:p-5">
              <div className="flex items-center gap-2 border-b border-[var(--glass-border)] pb-3 text-xs text-muted-foreground">
                <Languages className="size-4 text-violet-ink" /> Citizens write the way they speak
                <span className="ml-auto flex gap-1" aria-hidden>
                  <span className="size-2 rounded-full bg-magenta/70" />
                  <span className="size-2 rounded-full bg-violet/70" />
                  <span className="size-2 rounded-full bg-cyan/70" />
                </span>
              </div>
              <Stagger className="space-y-3" delay={0.3} gap={0.18}>
                {EXAMPLES.map((e) => (
                  <StaggerItem key={e.lang} className="rounded-2xl rounded-tl-md border border-[var(--glass-border)] bg-[var(--glass)] p-3.5">
                    <Badge tone={e.lang === "English" ? "cyan" : e.lang === "Hindi" ? "magenta" : "violet"} className="mb-1.5">
                      {e.lang}
                    </Badge>
                    <p className="text-sm leading-relaxed" lang={e.hi ? "hi" : undefined}>
                      {e.text}
                    </p>
                  </StaggerItem>
                ))}
              </Stagger>
              <p className="flex items-center gap-1.5 pt-1 text-xs text-muted-foreground">
                <MapPinned className="size-4 text-cyan-ink" /> Add a photo and a map pin - a tracking ID is issued instantly.
              </p>
            </Card>
          </div>
        </section>

        {meta.data && (
          <section aria-label="Complaint categories" className="pb-16">
            <p className="mb-4 text-center text-sm text-muted-foreground">
              {meta.data.categories.length} complaint categories routed to {meta.data.departments.length} departments across {meta.data.wards.length} wards
            </p>
            <Marquee speed={60}>
              {meta.data.categories.map((c) => (
                <span key={c.name} className="glass whitespace-nowrap rounded-full px-4 py-2 text-sm">
                  {c.name} <span className="text-muted-foreground">→ {c.department}</span>
                </span>
              ))}
            </Marquee>
          </section>
        )}

        <StatsStrip />

        <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <div className="mx-auto mb-10 max-w-2xl text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">What it does</p>
            <h2 className="mt-2 font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
              Built so officers can <span className="text-gradient">trust and check</span> every suggestion
            </h2>
          </div>
          <Reveal className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <Card key={title} data-reveal interactive className="p-5">
                <span className="grid size-11 place-items-center rounded-xl bg-grad-primary text-white shadow-[0_10px_24px_-10px_rgba(124,92,255,0.8)]">
                  <Icon className="size-5" />
                </span>
                <h3 className="mt-4 font-display text-lg font-semibold">{title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{text}</p>
              </Card>
            ))}
          </Reveal>
        </section>

        <HowItWorks />

        <section className="mx-auto max-w-4xl px-4 py-20 sm:px-6">
          <Reveal>
            <Card strong className="relative overflow-hidden px-6 py-12 text-center sm:px-12">
              <div aria-hidden className="absolute -top-20 left-1/2 h-40 w-3/4 -translate-x-1/2 rounded-full bg-violet/30 blur-3xl" />
              <h2 className="relative font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
                See it with the <span className="text-gradient">demo accounts</span>
              </h2>
              <p className="relative mx-auto mt-3 max-w-xl text-muted-foreground">
                File a complaint as a citizen, then switch to the officer account to review the AI suggestion, override it and retrain the model.
              </p>
              <div className="relative mt-7 flex flex-wrap justify-center gap-3">
                <Button asChild size="lg">
                  <Link to={cta}>
                    {user ? "Open dashboard" : "Log in"} <ArrowRight />
                  </Link>
                </Button>
              </div>
            </Card>
          </Reveal>
        </section>
      </main>

      <footer className="px-4 pb-10 text-center text-xs text-muted-foreground">
        CivicPulse · decision support, not decision making · Map tiles © OpenStreetMap contributors
      </footer>
    </div>
  );
}
