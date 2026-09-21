import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "motion/react";
import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/common/ThemeToggle";

const ROWS = 7;
const COLS = 8;
const PAPERS = ["var(--paper-1)", "var(--paper-2)", "var(--paper-3)", "var(--paper-4)"];

/** A decorative seat grid: four papers laid out so no two neighbours share one. */
function SeatGridArt() {
  const reduce = useReducedMotion();
  return (
    <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${COLS}, minmax(0, 1fr))` }} aria-hidden>
      {Array.from({ length: ROWS * COLS }, (_, i) => {
        const r = Math.floor(i / COLS);
        const c = i % COLS;
        const paper = PAPERS[(r % 2) * 2 + (c % 2)];
        return (
          <motion.span
            key={i}
            className="aspect-square rounded-md"
            style={{ backgroundColor: paper }}
            initial={reduce ? false : { opacity: 0, scale: 0.6 }}
            animate={{ opacity: 0.9, scale: 1 }}
            transition={{ delay: reduce ? 0 : (r + c) * 0.035, duration: 0.35, ease: "easeOut" }}
          />
        );
      })}
    </div>
  );
}

export function AuthShell({ title, subtitle, children, footer }: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="grid min-h-dvh lg:grid-cols-[1.05fr_1fr]">
      <div className="relative hidden overflow-hidden bg-[hsl(244_60%_14%)] p-10 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,hsl(244_80%_45%/0.55),transparent_60%)]" />
        <Link to="/" className="relative z-10 w-fit" aria-label="SeatWise home">
          <Logo className="text-white [&_.text-primary]:text-[#a5b4fc]" />
        </Link>
        <div className="relative z-10 mx-auto w-full max-w-md">
          <SeatGridArt />
          <div className="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-xs text-white/70">
            {["Paper A", "Paper B", "Paper C", "Paper D"].map((label, i) => (
              <span key={label} className="inline-flex items-center gap-1.5">
                <span className="size-2.5 rounded-sm" style={{ backgroundColor: PAPERS[i] }} />
                {label}
              </span>
            ))}
          </div>
        </div>
        <div className="relative z-10 max-w-md">
          <p className="font-display text-2xl font-semibold leading-snug">
            No two neighbours on the same paper. Every plan reproducible from its seed.
          </p>
          <p className="mt-3 text-sm text-white/65">Constraint-optimised exam seating, generated in seconds.</p>
        </div>
      </div>

      <div className="flex flex-col">
        <div className="flex items-center justify-between p-4 sm:p-6">
          <Link to="/" className="lg:invisible" aria-label="SeatWise home">
            <Logo />
          </Link>
          <ThemeToggle />
        </div>
        <div className="flex flex-1 items-center justify-center px-4 pb-10 sm:px-6">
          <motion.div
            className="w-full max-w-sm"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          >
            <h1 className="font-display text-2xl font-semibold sm:text-3xl">{title}</h1>
            <p className="mt-2 text-sm text-muted-foreground">{subtitle}</p>
            <div className="mt-8">{children}</div>
            {footer && <div className="mt-6 text-center text-sm text-muted-foreground">{footer}</div>}
          </motion.div>
        </div>
      </div>
    </div>
  );
}
