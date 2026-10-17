import { motion } from "framer-motion";
import { FileText, Quote } from "lucide-react";

import { LogoMark } from "@/components/brand/Logo";

const appear = (delay: number) => ({
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { delay, duration: 0.55, ease: [0.22, 1, 0.36, 1] as const },
});

/** Real exchange: the bundled sample_data/sample_notes_data_structures.txt, answered by the offline retriever. */
export function ExampleAnswer() {
  return (
    <div className="relative mx-auto w-full max-w-md">
      <div aria-hidden className="absolute -inset-8 rounded-[2.5rem] bg-grad-primary opacity-25 blur-3xl" />
      <div className="glass-strong sweep relative space-y-3 rounded-3xl p-4 sm:p-5">
        <div className="flex items-center gap-2 border-b border-[var(--glass-border)] pb-3 text-xs text-muted-foreground">
          <FileText className="size-4 shrink-0 text-violet-ink" /> <span className="truncate">sample_notes_data_structures.txt</span>
          <span className="ml-auto flex gap-1" aria-hidden>
            <span className="size-2 rounded-full bg-magenta/70" />
            <span className="size-2 rounded-full bg-violet/70" />
            <span className="size-2 rounded-full bg-cyan/70" />
          </span>
        </div>
        <motion.div
          {...appear(0.6)}
          className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-grad-primary px-3.5 py-2 text-sm text-white shadow-[0_8px_24px_-10px_rgba(124,92,255,0.8)]"
        >
          What is the LIFO principle?
        </motion.div>
        <motion.div {...appear(1.3)} className="flex gap-2">
          <LogoMark className="size-7" />
          <div className="min-w-0 space-y-2 rounded-2xl rounded-tl-md border border-[var(--glass-border)] bg-[var(--glass)] p-3 text-sm">
            <p>
              A stack is a linear data structure that follows the <strong>Last In First Out (LIFO)</strong> principle. A queue is a
              linear data structure that follows the First In First Out (FIFO) principle.
            </p>
          </div>
        </motion.div>
        <motion.div {...appear(2)} className="flex items-center gap-2 pl-9 text-xs text-muted-foreground">
          <Quote className="size-3.5 text-violet-ink" />
          <span className="truncate">Source: sample_notes_data_structures.txt</span>
        </motion.div>
      </div>
    </div>
  );
}
