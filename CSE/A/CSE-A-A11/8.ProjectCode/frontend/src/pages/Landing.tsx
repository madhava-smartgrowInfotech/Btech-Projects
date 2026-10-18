import { useQuery } from "@tanstack/react-query";
import { ArrowRight, FlaskConical, GitPullRequest, MessagesSquare, Play, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router";

import { ThemeButton } from "@/components/app/ThemeButton";
import { Logo } from "@/components/brand/Logo";
import { ExampleAnswer } from "@/components/landing/ExampleAnswer";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { StatsStrip } from "@/components/landing/StatsStrip";
import { FadeIn, Marquee, Parallax, Reveal, SlideUp, SmoothScroll } from "@/components/motion";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const FEATURES = [
  {
    icon: GitPullRequest,
    title: "PR review",
    text: "Paste a diff, compare two versions, drop a GitHub PR link or upload a repository. You get a verdict, a risk score, explanations and verified patches.",
    to: "/app/review",
    cta: "Review a pull request",
  },
  {
    icon: MessagesSquare,
    title: "Codebase assistant",
    text: "Ask “where is authentication handled?” and get files, functions and call flow, found with text similarity plus the import and call graph.",
    to: "/app/codebase",
    cta: "Ask your codebase",
  },
  {
    icon: FlaskConical,
    title: "Model lab",
    text: "The base paper, reproduced: 14 metrics, 7 feature selectors, SmoteTomek balancing and 9 models. Try any Python function and see why it scores as it does.",
    to: "/app/lab",
    cta: "Explore the model",
  },
];

export default function Landing() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const rules = useQuery({
    queryKey: ["public-rules"],
    queryFn: async () => (await api.get<{ rules: string[] }>("/public/rules")).data.rules,
    retry: false,
    staleTime: Infinity,
  });

  async function tryDemo() {
    if (user) return navigate("/app");
    setBusy(true);
    try {
      const creds = (await api.get<{ email: string; password: string }>("/auth/demo")).data;
      await login(creds.email, creds.password);
      navigate("/app");
    } catch (e) {
      toast.error(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative min-h-dvh overflow-x-clip">
      <AuroraBackground />
      <SmoothScroll />
      <a href="#content" className="sr-only z-[90] rounded-lg bg-popover px-3 py-2 focus:not-sr-only focus:fixed focus:left-3 focus:top-3">
        Skip to content
      </a>

      <header className="sticky top-0 z-40 px-3 pt-3">
        <nav aria-label="Primary" className="glass mx-auto flex h-14 max-w-6xl items-center gap-2 rounded-2xl px-3 sm:px-4">
          <Link to="/" aria-label="AutoSecAI home">
            <Logo />
          </Link>
          <div className="ml-6 hidden items-center gap-1 text-sm text-muted-foreground md:flex">
            <a href="#features" className="rounded-lg px-3 py-2 hover:bg-muted hover:text-foreground">Features</a>
            <a href="#how-it-works" className="rounded-lg px-3 py-2 hover:bg-muted hover:text-foreground">How it works</a>
          </div>
          <div className="ml-auto flex items-center gap-1.5">
            <ThemeButton />
            {user ? (
              <Button asChild size="sm">
                <Link to="/app">Open app <ArrowRight /></Link>
              </Button>
            ) : (
              <>
                <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
                  <Link to="/login">Sign in</Link>
                </Button>
                <Button size="sm" onClick={tryDemo} loading={busy}>
                  Try the demo
                </Button>
              </>
            )}
          </div>
        </nav>
      </header>

      <main id="content">
        <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-16 pt-14 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:pb-24 lg:pt-20">
          <div className="space-y-7">
            <SlideUp>
              <Badge tone="violet" className="px-3 py-1 text-xs">
                <ShieldCheck /> Multi-agent pull-request security review
              </Badge>
            </SlideUp>
            <SlideUp delay={0.08}>
              <h1 className="font-display text-4xl font-semibold leading-[1.05] tracking-tight text-balance sm:text-5xl lg:text-6xl">
                Review every pull request like a <span className="text-gradient">security engineer</span>
              </h1>
            </SlideUp>
            <SlideUp delay={0.16}>
              <p className="max-w-xl text-base text-muted-foreground sm:text-lg">
                AutoSecAI finds vulnerabilities with static analysis and taint tracking, scores risky functions with the metric model from the base
                paper, explains each flaw in plain language and proposes patches it has already re-scanned.
              </p>
            </SlideUp>
            <SlideUp delay={0.24} className="flex flex-wrap items-center gap-3">
              <Button size="lg" onClick={tryDemo} loading={busy}>
                <Play /> {user ? "Open the app" : "Try the live demo"}
              </Button>
              {!user && (
                <Button asChild size="lg" variant="secondary">
                  <Link to="/login">Sign in</Link>
                </Button>
              )}
            </SlideUp>
            <FadeIn delay={0.5} className="text-xs text-muted-foreground">
              The demo opens a ready account: no sign-up, nothing to configure. Code never leaves your machine unless you switch on LLM explanations.
            </FadeIn>
          </div>
          <Parallax offset={24}>
            <ExampleAnswer />
          </Parallax>
        </section>

        {rules.data && rules.data.length > 0 && (
          <section aria-label="Weakness classes AutoSecAI detects" className="pb-16">
            <Marquee speed={55}>
              {rules.data.map((r) => (
                <span key={r} className="glass whitespace-nowrap rounded-full px-4 py-2 text-sm text-muted-foreground">
                  {r}
                </span>
              ))}
            </Marquee>
          </section>
        )}

        <StatsStrip />

        <section id="features" className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
          <div className="mx-auto mb-12 max-w-2xl space-y-3 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">What you get</p>
            <h2 className="font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
              One review pipeline, <span className="text-gradient">three ways in</span>
            </h2>
          </div>
          <Reveal className="grid gap-5 md:grid-cols-3">
            {FEATURES.map(({ icon: Icon, title, text, to, cta }) => (
              <Card key={title} interactive data-reveal className="flex flex-col gap-4 p-6">
                <span className="grid size-12 place-items-center rounded-2xl bg-grad-primary text-white shadow-[0_12px_30px_-10px_rgba(124,92,255,0.9)]">
                  <Icon className="size-6" />
                </span>
                <h3 className="font-display text-xl font-semibold">{title}</h3>
                <p className="flex-1 text-sm text-muted-foreground">{text}</p>
                <Link to={to} className="inline-flex items-center gap-1 text-sm font-medium text-violet-ink hover:underline">
                  {cta} <ArrowRight className="size-4" />
                </Link>
              </Card>
            ))}
          </Reveal>
        </section>

        <HowItWorks />

        <section className="mx-auto max-w-4xl px-4 pb-24 sm:px-6">
          <Reveal>
            <Card strong className="relative overflow-hidden px-6 py-12 text-center sm:px-12">
              <div aria-hidden className="absolute -top-24 left-1/2 h-48 w-2/3 -translate-x-1/2 rounded-full bg-violet/30 blur-3xl" />
              <h2 className="relative font-display text-3xl font-semibold text-balance">See it block a vulnerable pull request in seconds</h2>
              <p className="relative mx-auto mt-3 max-w-lg text-muted-foreground">
                The demo review runs on a deliberately vulnerable Flask change. Open the findings, read the patch, export the PR comment.
              </p>
              <div className="relative mt-7">
                <Button size="lg" onClick={tryDemo} loading={busy}>
                  <Play /> {user ? "Open the app" : "Start the demo"}
                </Button>
              </div>
            </Card>
          </Reveal>
        </section>
      </main>

      <footer className="border-t border-[var(--glass-border)] py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 text-sm text-muted-foreground sm:flex-row sm:px-6">
          <Logo />
          <p className="text-center sm:text-right">
            CSE-A · Batch 11 · Based on “Leveraging Key Source Code Metrics for Predicting Software Vulnerabilities With ML”, IEEE Access 2026.
          </p>
        </div>
      </footer>
    </div>
  );
}

