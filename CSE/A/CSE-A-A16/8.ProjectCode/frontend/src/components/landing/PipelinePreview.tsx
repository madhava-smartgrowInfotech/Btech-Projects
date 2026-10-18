import { motion } from "framer-motion";
import { ArrowRight, Volume2 } from "lucide-react";
import type { ReactNode } from "react";

import { LogoMark } from "@/components/brand/Logo";

const appear = (delay: number) => ({
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { delay, duration: 0.55, ease: [0.22, 1, 0.36, 1] as const },
});

const HAND =
  "M11 25.5c-1.7-1.5-3-3.6-3.4-5.2l-.9-3.6c-.2-.9.9-1.5 1.5-.8l1.6 1.9V9.4a1.3 1.3 0 0 1 2.6 0V15h.5V7.9a1.3 1.3 0 0 1 2.6 0V15h.5V8.9a1.3 1.3 0 0 1 2.6 0V15h.5v-3.6a1.3 1.3 0 0 1 2.6 0v7.2c0 3.2-1.9 5.9-4.7 6.9-2.2.8-4.3.4-6-.1Z";

function Stage({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex min-w-0 flex-1 flex-col items-center gap-1.5">
      <div className="grid aspect-square w-full max-w-[104px] place-items-center overflow-hidden rounded-2xl border border-[var(--glass-border)]">
        {children}
      </div>
      <span className="text-[11px] font-medium text-muted-foreground">{label}</span>
    </div>
  );
}

/** Decorative walk through the pipeline (illustration only - no measured values). */
export function PipelinePreview() {
  const sentence = "HELLO";
  return (
    <div className="relative mx-auto w-full max-w-md">
      <div aria-hidden className="absolute -inset-3 rounded-[2.5rem] sm:-inset-8 bg-grad-primary opacity-25 blur-3xl" />
      <div className="glass-strong sweep relative space-y-4 rounded-3xl p-4 sm:p-5">
        <div className="flex items-center gap-2 border-b border-[var(--glass-border)] pb-3 text-xs text-muted-foreground">
          <LogoMark className="size-5" /> Live recognition · pipeline illustration
          <span className="ml-auto flex gap-1" aria-hidden>
            <span className="size-2 rounded-full bg-magenta/70" />
            <span className="size-2 rounded-full bg-violet/70" />
            <span className="size-2 rounded-full bg-cyan/70" />
          </span>
        </div>

        <motion.div {...appear(0.3)} className="flex items-center gap-1.5 sm:gap-2" aria-hidden>
          <Stage label="1 · ROI crop">
            <svg viewBox="0 0 32 32" className="size-full bg-[#0f172a]">
              <rect x="3" y="3" width="26" height="26" rx="2" fill="none" stroke="#22D3EE" strokeWidth="1" />
              <path d={HAND} fill="#e8c4a0" transform="translate(0 1)" />
            </svg>
          </Stage>
          <ArrowRight className="size-4 shrink-0 text-muted-foreground" />
          <Stage label="2 · Segmented">
            <svg viewBox="0 0 32 32" className="size-full bg-black">
              <path d={HAND} fill="#fff" transform="translate(0 1)" />
            </svg>
          </Stage>
          <ArrowRight className="size-4 shrink-0 text-muted-foreground" />
          <Stage label="3 · CNN">
            <div className="grid size-full place-items-center bg-grad-primary font-display text-5xl font-bold text-white">H</div>
          </Stage>
        </motion.div>

        <motion.div {...appear(0.9)} className="space-y-2">
          <div className="text-xs font-medium text-muted-foreground">Sentence</div>
          <div className="flex items-center gap-2 rounded-2xl border border-[var(--glass-border)] bg-[var(--glass)] px-3 py-2.5">
            <span className="flex flex-1 gap-1 font-display text-xl font-semibold tracking-widest" aria-label={`Example sentence: ${sentence}`}>
              {sentence.split("").map((ch, i) => (
                <motion.span key={i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.2 + i * 0.35 }}>
                  {ch}
                </motion.span>
              ))}
              <motion.span
                aria-hidden
                className="ml-0.5 inline-block h-6 w-0.5 self-center bg-cyan"
                animate={{ opacity: [1, 0, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
              />
            </span>
            <span className="grid size-8 place-items-center rounded-lg bg-grad-primary text-white">
              <Volume2 className="size-4" />
            </span>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
