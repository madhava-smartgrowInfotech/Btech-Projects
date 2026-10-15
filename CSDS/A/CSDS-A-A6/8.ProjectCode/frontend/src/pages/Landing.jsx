import { Link } from "react-router";
import { FileText, FileWarning, Gauge, GitGraph } from "lucide-react";

import { HowItWorks } from "@/components/landing/HowItWorks";
import { StatsStrip } from "@/components/landing/StatsStrip";
import { FadeIn, MagneticButton, SlideUp, Stagger, StaggerItem } from "@/components/motion";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useAuth } from "@/lib/auth";

const FEATURES = [
  {
    icon: FileText,
    title: "Upload & segment",
    desc: "Upload a PDF or DOCX contract. ClauseGuard splits it into clauses with page numbers and classifies each one.",
  },
  {
    icon: FileWarning,
    title: "Predatory clause detection",
    desc: "Flags restraint of trade, penalty clauses, unilateral termination, unlimited liability, one-sided arbitration, auto-renewal and IP overreach under Indian contract law.",
  },
  {
    icon: GitGraph,
    title: "Risky combinations",
    desc: "A clause graph shows combinations that are harmless alone but dangerous together, such as unilateral termination plus no-refund plus penalty.",
  },
  {
    icon: Gauge,
    title: "Complexity grade",
    desc: "Readability, legalese density, cross-references and sentence length combine into an A-F grade with a plain summary.",
  },
];

export default function Landing() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="space-y-24">
      <section className="pt-8 text-center sm:pt-14">
        <SlideUp>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Contract risk, in plain language</p>
        </SlideUp>
        <FadeIn delay={0.1}>
          <h1 className="mt-4 font-display text-4xl font-semibold tracking-tight text-balance sm:text-6xl">
            Know what you&apos;re <span className="text-gradient">signing.</span>
          </h1>
        </FadeIn>
        <SlideUp delay={0.2}>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-muted-foreground">
            ClauseGuard scores contract complexity and flags predatory clauses in plain language, built for Indian agreements.
          </p>
        </SlideUp>
        <div className="mt-9 flex flex-wrap justify-center gap-3">
          <MagneticButton>
            <Button asChild size="lg">
              <Link to={isAuthenticated ? "/app/upload" : "/register"}>{isAuthenticated ? "Upload a contract" : "Get started"}</Link>
            </Button>
          </MagneticButton>
          <Button asChild size="lg" variant="outline">
            <Link to="/evaluation">See evaluation results</Link>
          </Button>
        </div>
      </section>

      <Stagger className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((f) => (
          <StaggerItem key={f.title}>
            <Card interactive className="h-full p-5">
              <span className="grid size-11 place-items-center rounded-xl bg-grad-primary text-white shadow-[0_8px_24px_-8px_rgba(124,92,255,0.7)]">
                <f.icon className="size-5" />
              </span>
              <h3 className="mt-4 font-display text-lg font-semibold">{f.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{f.desc}</p>
            </Card>
          </StaggerItem>
        ))}
      </Stagger>

      <StatsStrip />
      <HowItWorks />
    </div>
  );
}
