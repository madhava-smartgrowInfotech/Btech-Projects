import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Leaf, ShieldCheck, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";
import { toast } from "sonner";

import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/app/ThemeToggle";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { StatsStrip } from "@/components/landing/StatsStrip";
import { CountUp } from "@/components/motion/CountUp";
import { Marquee } from "@/components/motion/Marquee";
import { SlideUp } from "@/components/motion/SlideUp";
import { SmoothScroll } from "@/components/motion/SmoothScroll";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { DEMO_EMAIL, DEMO_PASSWORD } from "@/lib/demo";
import { evaluationQuery, label } from "@/lib/evaluation";
import api from "@/lib/api";
import { keys } from "@/lib/queries";
import type { ProfileOptions } from "@/lib/types";

const GUARDRAILS = [
  { title: "Calorie floor", text: "Targets never drop below 1200 kcal (women) or 1500 kcal (men)." },
  { title: "Allergens blocked first", text: "Allergen dishes are removed before the optimiser runs, then checked again after it." },
  { title: "Condition limits", text: "Diabetes, hypertension and high cholesterol add sodium, glycaemic-load and fat limits." },
  { title: "AI output is scanned", text: "Recipes written by Gemini are checked for allergen words and diet conflicts before you see them." },
];

export default function Landing() {
  const { login } = useAuth();
  const [trying, setTrying] = useState(false);
  const options = useQuery({
    queryKey: keys.profileOptions,
    queryFn: async () => (await api.get<ProfileOptions>("/profile/options")).data,
    staleTime: 60 * 60_000,
  });
  const evaluation = useQuery(evaluationQuery);

  const allergens = options.data?.allergies.map((a) => `${label(a)} free`) ?? [];
  const sampleKcal = evaluation.data?.requirements.demo_profile_target_kcal;

  async function trySample() {
    setTrying(true);
    try {
      await login(DEMO_EMAIL, DEMO_PASSWORD);
    } catch (err) {
      toast.error(errorMessage(err));
      setTrying(false);
    }
  }

  return (
    <div className="relative min-h-dvh overflow-x-hidden">
      <SmoothScroll />
      <AuroraBackground />

      <header className="sticky top-0 z-30 px-3 pt-3 sm:px-6">
        <div className="glass mx-auto flex h-14 max-w-6xl items-center gap-2 rounded-2xl px-3">
          <Link to="/" aria-label="NutriSense home" className="mr-auto">
            <Logo />
          </Link>
          <ThemeToggle />
          <Button asChild variant="ghost" size="sm" magnetic={false}>
            <Link to="/login">Log in</Link>
          </Button>
          <Button asChild size="sm">
            <Link to="/register">Get started</Link>
          </Button>
        </div>
      </header>

      <main id="main">
        <section className="mx-auto grid max-w-6xl items-center gap-10 px-4 pb-16 pt-12 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:pt-20">
          <SlideUp className="space-y-6">
            <Badge tone="violet" className="px-3 py-1 text-xs">
              <Sparkles /> Indian meal plans · calorie-true · allergy-safe
            </Badge>
            <h1 className="font-display text-4xl font-semibold leading-[1.05] tracking-tight text-balance sm:text-5xl lg:text-6xl">
              Eat the Indian food you love, at the calories <span className="text-gradient">your body needs</span>.
            </h1>
            <p className="max-w-xl text-base text-muted-foreground sm:text-lg">
              NutriSense builds a week of North or South Indian meals that hit your daily calories and macros, respects your allergies and
              health conditions, and adjusts as your weight changes.
            </p>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button asChild size="lg">
                <Link to="/register">
                  Get started <ArrowRight />
                </Link>
              </Button>
              <Button variant="secondary" size="lg" onClick={trySample} loading={trying}>
                Try the sample account
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">Sample account: {DEMO_EMAIL} · clearly labelled sample data.</p>
          </SlideUp>

          <SlideUp delay={0.1}>
            <Card strong className="relative overflow-hidden p-6 sm:p-8">
              <div aria-hidden className="absolute -right-16 -top-16 size-56 rounded-full bg-cyan/25 blur-3xl" />
              <div className="relative space-y-5">
                <div className="flex items-center gap-3">
                  <span className="grid size-10 place-items-center rounded-xl bg-grad-primary text-white">
                    <Leaf className="size-5" />
                  </span>
                  <div>
                    <p className="text-sm font-medium">Sample profile</p>
                    <p className="text-xs text-muted-foreground">28, female, vegetarian, peanut allergy, weight loss</p>
                  </div>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">Daily calorie target</p>
                  <p className="font-display text-5xl font-semibold tabular-nums">
                    {sampleKcal !== undefined ? <CountUp value={sampleKcal} /> : <span className="text-muted-foreground">-</span>}
                    <span className="ml-2 text-lg font-medium text-muted-foreground">kcal</span>
                  </p>
                </div>
                <div className="flex items-start gap-3 rounded-2xl border border-[var(--glass-border)] bg-grad-soft p-4 text-sm">
                  <ShieldCheck className="mt-0.5 size-5 shrink-0 text-violet-ink" />
                  <p>
                    {evaluation.data
                      ? `${evaluation.data.meal_plans.safety.allergen_violations} allergen violations across ${evaluation.data.meal_plans.plans_built} generated plans in our test run.`
                      : "Allergens are blocked before any dish is chosen."}
                  </p>
                </div>
              </div>
            </Card>
          </SlideUp>
        </section>

        {allergens.length > 0 && (
          <section aria-label="Allergen filters" className="py-4">
            <Marquee speed={45} className="gap-3">
              {allergens.map((a) => (
                <Badge key={a} tone="neutral" className="px-3 py-1.5 text-sm">
                  {a}
                </Badge>
              ))}
            </Marquee>
          </section>
        )}

        <section className="py-16">
          <StatsStrip />
        </section>

        <section className="py-16">
          <HowItWorks />
        </section>

        <section aria-labelledby="safety-title" className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
          <div className="mx-auto mb-10 max-w-2xl space-y-3 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Safety first</p>
            <h2 id="safety-title" className="font-display text-2xl font-semibold tracking-tight sm:text-4xl">
              Guardrails that run on every plan
            </h2>
          </div>
          <ul className="grid gap-4 sm:grid-cols-2">
            {GUARDRAILS.map((g) => (
              <li key={g.title} className="list-none">
                <Card className="flex h-full gap-4 p-5">
                  <ShieldCheck className="mt-0.5 size-5 shrink-0 text-violet-ink" />
                  <div className="space-y-1">
                    <h3 className="font-display font-semibold">{g.title}</h3>
                    <p className="text-sm text-muted-foreground">{g.text}</p>
                  </div>
                </Card>
              </li>
            ))}
          </ul>
        </section>

        <section className="mx-auto max-w-4xl px-4 pb-20 sm:px-6">
          <Card strong className="relative overflow-hidden px-6 py-12 text-center">
            <div aria-hidden className="absolute inset-x-1/4 -top-20 h-40 rounded-full bg-magenta/25 blur-3xl" />
            <div className="relative space-y-5">
              <h2 className="font-display text-2xl font-semibold tracking-tight sm:text-3xl">Build your first week in about two minutes</h2>
              <p className="mx-auto max-w-xl text-sm text-muted-foreground">Create a free account, complete the profile, and generate your plan.</p>
              <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
                <Button asChild size="lg">
                  <Link to="/register">
                    Create an account <ArrowRight />
                  </Link>
                </Button>
                <Button asChild variant="secondary" size="lg">
                  <Link to="/login">I already have an account</Link>
                </Button>
              </div>
            </div>
          </Card>
        </section>
      </main>

      <footer className="mx-auto max-w-6xl px-4 pb-10 text-center text-xs text-muted-foreground sm:px-6">
        NutriSense gives general nutrition guidance, not medical advice. If you have a medical condition, are pregnant or take medication, check
        your plan with a doctor or registered dietitian.
      </footer>
    </div>
  );
}
