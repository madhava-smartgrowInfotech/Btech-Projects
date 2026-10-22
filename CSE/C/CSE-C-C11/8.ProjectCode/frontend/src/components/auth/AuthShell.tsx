import { LineChart, PiggyBank, ShieldCheck, Sparkles } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { SlideUp } from "@/components/motion/SlideUp";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

const POINTS = [
  { icon: LineChart, text: "Dashboard, trends and a 0-100 financial health score" },
  { icon: Sparkles, text: "AI that sorts your expenses and answers questions about your money" },
  { icon: PiggyBank, text: "Budgets, goals and investments in one place" },
  { icon: ShieldCheck, text: "Passwords are hashed; every account only ever sees its own data" },
];

/** Shared frame for the login and signup screens: glass form card beside the product pitch. */
export function AuthShell({ title, subtitle, children, footer }: { title: string; subtitle: string; children: ReactNode; footer: ReactNode }) {
  return (
    <div className="relative min-h-dvh overflow-x-clip">
      <AuroraBackground />
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Link to="/" aria-label="FINJARVIS home">
          <Logo />
        </Link>
        <ThemeToggle />
      </header>
      <main className="mx-auto grid max-w-6xl items-center gap-10 px-4 pb-16 pt-4 sm:px-6 lg:min-h-[calc(100dvh-5rem)] lg:grid-cols-[1fr_1.05fr] lg:gap-16">
        <SlideUp className="order-2 hidden space-y-6 lg:order-1 lg:block">
          <h2 className="font-display text-4xl font-semibold leading-tight tracking-tight text-balance">
            Know where every rupee goes, <span className="text-gradient">before the month ends</span>
          </h2>
          <ul className="space-y-3">
            {POINTS.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-start gap-3 text-muted-foreground">
                <span className="mt-0.5 grid size-8 shrink-0 place-items-center rounded-xl bg-grad-soft text-violet-ink ring-1 ring-[var(--glass-border)]">
                  <Icon className="size-4" />
                </span>
                <span>{text}</span>
              </li>
            ))}
          </ul>
        </SlideUp>
        <SlideUp delay={0.08} className="order-1 mx-auto w-full max-w-md lg:order-2 lg:ml-auto">
          <div className="glass-strong relative overflow-hidden rounded-3xl p-6 sm:p-8">
            <div aria-hidden className="absolute -top-16 left-1/2 h-32 w-3/4 -translate-x-1/2 rounded-full bg-grad-primary opacity-25 blur-3xl" />
            <div className="relative space-y-1.5">
              <h1 className="font-display text-2xl font-semibold tracking-tight">{title}</h1>
              <p className="text-sm text-muted-foreground">{subtitle}</p>
            </div>
            <div className="relative mt-6">{children}</div>
          </div>
          <p className="mt-4 text-center text-sm text-muted-foreground">{footer}</p>
        </SlideUp>
      </main>
    </div>
  );
}
