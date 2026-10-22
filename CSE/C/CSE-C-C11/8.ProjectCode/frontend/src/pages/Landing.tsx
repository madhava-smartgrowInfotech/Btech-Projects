import { ArrowRight, BarChart3, Bell, Bot, FileText, Gauge, LineChart, Sparkles, Target, Wallet } from "lucide-react";
import { Link } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { ExampleAnswer } from "@/components/landing/ExampleAnswer";
import { HeroPreview } from "@/components/landing/HeroPreview";
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
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { useAuth } from "@/lib/auth";

const FEATURES = [
  { icon: Gauge, title: "Financial health score", text: "A 0-100 score from six weighted factors: savings, spending ratio, budgets, cash cushion, diversification and goals. It tells you which one is holding you back." },
  { icon: Sparkles, title: "Expenses sort themselves", text: "Type Swiggy order and it lands in Food. Correct it once and the model learns your habits." },
  { icon: Wallet, title: "Budgets with early warnings", text: "Monthly limits per category, with alerts at 75, 90 and 100 percent so you can act before you overspend." },
  { icon: LineChart, title: "Honest forecasts", text: "Next month's spending from a linear trend. With fewer than three months of history it says so instead of inventing a number." },
  { icon: Target, title: "Goals and investments", text: "See the monthly saving each goal needs, track holdings with optional live prices, and watch net worth move." },
  { icon: FileText, title: "Reports you can keep", text: "Export a monthly PDF, an Excel workbook, or every transaction as CSV." },
];

const TECH = ["TF-IDF + Logistic Regression", "Linear-trend forecast", "Six-factor health score", "SQLite, runs offline", "bcrypt-hashed passwords", "PDF · Excel · CSV reports", "Optional LLM answers"];

export default function Landing() {
  const { user } = useAuth();
  return (
    <div className="relative overflow-x-clip">
      <SmoothScroll />
      <AuroraBackground />
      <a href="#top" className="sr-only z-[90] rounded-lg bg-popover px-3 py-2 focus:not-sr-only focus:fixed focus:left-3 focus:top-3">
        Skip to content
      </a>

      <header className="sticky top-0 z-40 px-3 pt-3">
        <div className="glass mx-auto flex h-14 max-w-6xl items-center gap-2 rounded-2xl px-3 sm:px-4">
          <Link to="/" aria-label="FINJARVIS home">
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
            {user ? (
              <Button asChild size="sm">
                <Link to="/app">
                  Open dashboard <ArrowRight />
                </Link>
              </Button>
            ) : (
              <>
                <Button asChild size="sm" variant="ghost" className="hidden sm:inline-flex">
                  <Link to="/login">Log in</Link>
                </Button>
                <Button asChild size="sm">
                  <Link to="/signup">
                    Get started <ArrowRight />
                  </Link>
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
                <Sparkles aria-hidden /> AI-powered personal finance
              </Badge>
            </SlideUp>
            <SlideUp delay={0.08}>
              <h1 className="font-display text-4xl font-semibold leading-[1.05] tracking-tight text-balance sm:text-5xl lg:text-6xl">
                Your money, <span className="text-gradient">finally explained</span>
              </h1>
            </SlideUp>
            <SlideUp delay={0.16}>
              <p className="max-w-xl text-lg text-muted-foreground">
                FINJARVIS tracks what you spend, sorts it with AI, warns you before a budget breaks, and answers questions about your own finances. It
                runs on your computer, and your data stays there.
              </p>
            </SlideUp>
            <SlideUp delay={0.24} className="flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link to="/signup">
                  Create free account <ArrowRight />
                </Link>
              </Button>
              <Button asChild size="lg" variant="secondary">
                <Link to="/login">
                  <Bot /> Try the demo account
                </Link>
              </Button>
            </SlideUp>
          </div>
          <SlideUp delay={0.3}>
            <HeroPreview />
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
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">What you get</p>
            <h2 className="font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
              Everything in one place, <span className="text-gradient">nothing invented</span>
            </h2>
          </Reveal>
          <Stagger inView className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
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

        <section className="mx-auto grid max-w-6xl items-center gap-10 px-4 pb-16 sm:px-6 lg:grid-cols-2 lg:gap-16">
          <Reveal className="space-y-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Ask in plain words</p>
            <h2 className="font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
              Answers from <span className="text-gradient">your numbers</span>, not guesses
            </h2>
            <p className="max-w-md text-muted-foreground">
              The assistant calculates from your own transactions, budgets and goals. It never makes up a figure, and it always reminds you it is not a
              certified financial advisor.
            </p>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-center gap-2"><BarChart3 className="size-4 text-violet-ink" /> Where am I spending the most money?</li>
              <li className="flex items-center gap-2"><Target className="size-4 text-violet-ink" /> Can I save 10000 this month?</li>
              <li className="flex items-center gap-2"><Bell className="size-4 text-violet-ink" /> What is my financial health?</li>
            </ul>
          </Reveal>
          <ExampleAnswer />
        </section>

        <section className="mx-auto max-w-4xl px-4 pb-24 sm:px-6">
          <Reveal>
            <div className="glass-strong relative overflow-hidden rounded-3xl px-6 py-12 text-center sm:px-12">
              <div aria-hidden className="absolute -top-20 left-1/2 h-40 w-3/4 -translate-x-1/2 rounded-full bg-grad-primary opacity-30 blur-3xl" />
              <h2 className="relative font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
                Take control of your month, <span className="text-gradient">starting today</span>
              </h2>
              <p className="relative mx-auto mt-3 max-w-lg text-muted-foreground">
                Everything runs on your own computer. Sign up, or use the demo account to look around first.
              </p>
              <div className="relative mt-6 flex flex-wrap justify-center gap-3">
                <Button asChild size="lg">
                  <Link to="/signup">
                    Get started <ArrowRight />
                  </Link>
                </Button>
                <Button asChild size="lg" variant="secondary">
                  <Link to="/login">Log in</Link>
                </Button>
              </div>
            </div>
          </Reveal>
        </section>
      </main>

      <footer className="border-t border-[var(--glass-border)] px-4 py-8 text-center text-sm text-muted-foreground">
        FINJARVIS · AI Based Personal Finance Manager · informational analysis only, not professional financial advice.
      </footer>
    </div>
  );
}
