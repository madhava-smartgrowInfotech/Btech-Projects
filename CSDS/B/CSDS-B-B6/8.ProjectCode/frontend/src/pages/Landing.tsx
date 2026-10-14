import { Bell, Bot, Building2, FileJson, Fingerprint, HeartPulse, RefreshCcw, ShieldCheck } from "lucide-react";
import { Link } from "react-router";

import { ExampleAnswer } from "@/components/landing/ExampleAnswer";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { StatsStrip } from "@/components/landing/StatsStrip";
import { Logo } from "@/components/brand/Logo";
import { FadeIn } from "@/components/motion/FadeIn";
import { Parallax } from "@/components/motion/Parallax";
import { SlideUp } from "@/components/motion/SlideUp";
import { SmoothScroll } from "@/components/motion/SmoothScroll";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { HOME, useAuth } from "@/lib/auth";

const FEATURES = [
  { icon: Building2, title: "Connected hospitals", text: "Three independent HL7 FHIR R4 servers, each with its own database and patient IDs." },
  { icon: Fingerprint, title: "Master Patient Index", text: "Fuzzy matching on name, birth date, gender and phone links one person across hospitals, with a confidence score." },
  { icon: ShieldCheck, title: "Consent you control", text: "Grant or revoke access per hospital and data category, stored as FHIR Consent in a tamper-evident ledger." },
  { icon: FileJson, title: "Secure retrieval", text: "Doctors pass a consent check before FHIR calls fetch and merge records. Every access is audited." },
  { icon: RefreshCcw, title: "Post-treatment sync", text: "Hospitals push a FHIR summary after treatment and keep ownership of the original record." },
  { icon: HeartPulse, title: "Risk prediction", text: "Random Forest models estimate heart-disease and diabetes risk from values in the record, with the factors behind each score." },
  { icon: Bot, title: "AI assistant", text: "Plain-language explanations of lab reports and treatment summaries, in the patient's language." },
  { icon: Bell, title: "Reminders", text: "Medication and follow-up reminders built from prescriptions and care plans." },
];

export default function Landing() {
  const { user } = useAuth();
  return (
    <>
      <AuroraBackground />
      <SmoothScroll />

      <header className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-4 sm:px-6">
        <Link to="/" aria-label="UniHealth home">
          <Logo />
        </Link>
        <div className="flex items-center gap-2">
          <a href="#how-it-works" className="hidden rounded-lg px-3 py-2 text-sm text-muted-foreground hover:text-foreground sm:inline-block">
            How it works
          </a>
          <Button asChild size="sm">
            <Link to={user ? HOME[user.role] : "/login"}>{user ? "Open dashboard" : "Sign in"}</Link>
          </Button>
        </div>
      </header>

      <section className="mx-auto grid max-w-6xl items-center gap-12 overflow-hidden px-4 pb-16 pt-8 sm:px-6 lg:grid-cols-2 lg:pt-16">
        <div className="space-y-6">
          <FadeIn>
            <Badge tone="violet" className="px-3 py-1 text-xs">
              Synthetic sample data · three hospitals · consent first
            </Badge>
          </FadeIn>
          <SlideUp>
            <h1 className="font-display text-4xl font-semibold tracking-tight text-balance sm:text-6xl">
              One health record. <span className="text-gradient">Every hospital.</span> Your consent.
            </h1>
          </SlideUp>
          <SlideUp delay={0.1}>
            <p className="max-w-xl text-lg text-muted-foreground">
              UniHealth brings a patient's records from different hospitals into one timeline over HL7 FHIR, lets the patient decide who may see what,
              and explains results in plain language.
            </p>
          </SlideUp>
          <SlideUp delay={0.2} className="flex flex-wrap gap-3">
            <Button size="lg" asChild>
              <Link to="/login">Try the demo</Link>
            </Button>
            <Button size="lg" variant="secondary" asChild>
              <a href="#how-it-works">How it works</a>
            </Button>
          </SlideUp>
        </div>
        <Parallax offset={30}>
          <ExampleAnswer />
        </Parallax>
      </section>

      <section className="pb-20">
        <StatsStrip />
      </section>

      <HowItWorks />

      <section id="features" className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
        <div className="mb-10 max-w-2xl space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">What it does</p>
          <h2 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">Eight features, one consent model</h2>
        </div>
        <Stagger inView className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" gap={0.07}>
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <StaggerItem key={title}>
              <Card interactive className="h-full p-5">
                <span className="grid size-10 place-items-center rounded-xl bg-grad-soft text-violet-ink [&_svg]:size-5">
                  <Icon />
                </span>
                <h3 className="mt-4 font-display font-semibold">{title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{text}</p>
              </Card>
            </StaggerItem>
          ))}
        </Stagger>
      </section>

      <footer className="px-4 pb-10 text-center text-xs text-muted-foreground">
        Clinical decision support only. AI and risk outputs assist qualified professionals and are never a final diagnosis. Patient data shown is
        synthetic sample data (Synthea).
      </footer>
    </>
  );
}
