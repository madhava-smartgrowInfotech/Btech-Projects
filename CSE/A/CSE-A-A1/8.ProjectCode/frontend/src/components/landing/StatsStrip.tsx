import { BarChart3, FileType2, HardDrive, ListChecks, Route } from "lucide-react";
import type { ReactNode } from "react";

import { CountUp } from "@/components/motion/CountUp";
import { Reveal } from "@/components/motion/Reveal";

/** Facts taken straight from the backend configuration (config.py / quiz_generator.py / app.py). */
const FACTS: { icon: ReactNode; label: string; value: number; format: (n: number) => string }[] = [
  { icon: <FileType2 />, label: "File types: PDF, DOCX, TXT", value: 3, format: (n) => String(Math.round(n)) },
  { icon: <HardDrive />, label: "Max upload size", value: 16, format: (n) => `${Math.round(n)} MB` },
  { icon: <ListChecks />, label: "Questions per quiz", value: 5, format: (n) => String(Math.round(n)) },
  { icon: <Route />, label: "Roadmap priority levels", value: 3, format: (n) => String(Math.round(n)) },
  { icon: <BarChart3 />, label: "Passages retrieved per question", value: 4, format: (n) => String(Math.round(n)) },
];

/** What the platform does in numbers - read from the product's real limits, nothing measured or invented. */
export function StatsStrip() {
  return (
    <section aria-labelledby="stats-title" className="mx-auto max-w-6xl px-4 sm:px-6">
      <div className="glass relative overflow-hidden rounded-3xl px-5 py-8 sm:px-8">
        <div aria-hidden className="absolute -top-24 left-1/2 h-48 w-2/3 -translate-x-1/2 rounded-full bg-violet/25 blur-3xl" />
        <div className="relative mb-6 flex flex-col gap-1 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Built to run anywhere</p>
          <h2 id="stats-title" className="font-display text-xl font-semibold sm:text-2xl">
            Works offline with no API key
          </h2>
          <p className="text-sm text-muted-foreground">Retrieval uses TF-IDF and cosine similarity on your own machine. Claude answers are optional.</p>
        </div>
        <Reveal className="relative grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-3 lg:grid-cols-5">
          {FACTS.map((s) => (
            <div key={s.label} data-reveal className="flex flex-col items-center gap-1.5 text-center">
              <span className="text-violet-ink [&_svg]:size-4">{s.icon}</span>
              <span className="font-display text-2xl font-semibold sm:text-3xl">
                <CountUp value={s.value} format={s.format} className="text-gradient" />
              </span>
              <span className="text-xs text-muted-foreground">{s.label}</span>
            </div>
          ))}
        </Reveal>
      </div>
    </section>
  );
}
