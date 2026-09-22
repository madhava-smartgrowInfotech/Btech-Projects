import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/layout/ThemeToggle";

const POINTS = [
  "Readings from phones and sensor nodes, classified Strong / Weak / Dead",
  "The nearest better-signal spot, predicted around you",
  "Complaints filed automatically - with the evidence engineers need",
];

export function AuthLayout({ title, subtitle, children, footer }: { title: string; subtitle: string; children: ReactNode; footer: ReactNode }) {
  return (
    <div className="grid min-h-dvh lg:grid-cols-[1.05fr_1fr]">
      <aside className="relative hidden overflow-hidden bg-[hsl(231_60%_12%)] p-10 text-white lg:flex lg:flex-col">
        <div className="absolute inset-0 opacity-40 [background:radial-gradient(60%_50%_at_30%_20%,hsl(231_100%_62%/.55),transparent),radial-gradient(40%_40%_at_80%_80%,hsl(189_94%_45%/.35),transparent)]" aria-hidden />
        <svg className="absolute -right-24 top-1/2 h-[520px] w-[520px] -translate-y-1/2 opacity-[0.12]" viewBox="0 0 200 200" aria-hidden>
          {[30, 55, 80, 105].map((r) => (
            <circle key={r} cx="100" cy="100" r={r} fill="none" stroke="white" strokeWidth="1.2" />
          ))}
        </svg>
        <Link to="/" className="relative z-10 text-white">
          <Logo />
        </Link>
        <div className="relative z-10 mt-auto max-w-md">
          <h2 className="text-3xl font-bold leading-tight">Every weak signal, found. Every complaint, backed by data.</h2>
          <ul className="mt-6 space-y-3 text-sm text-white/80">
            {POINTS.map((p, i) => (
              <motion.li key={p} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 + i * 0.1 }} className="flex gap-3">
                <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-[hsl(189_94%_55%)]" aria-hidden />
                {p}
              </motion.li>
            ))}
          </ul>
        </div>
      </aside>

      <main className="flex flex-col px-4 py-6 sm:px-8">
        <div className="flex items-center justify-between">
          <Link to="/" className="lg:invisible" aria-label="SignalScout home">
            <Logo />
          </Link>
          <ThemeToggle />
        </div>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="mx-auto my-auto w-full max-w-sm py-10">
          <h1 className="text-2xl font-bold">{title}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
          <div className="mt-6">{children}</div>
          <div className="mt-6 text-center text-sm text-muted-foreground">{footer}</div>
        </motion.div>
      </main>
    </div>
  );
}
