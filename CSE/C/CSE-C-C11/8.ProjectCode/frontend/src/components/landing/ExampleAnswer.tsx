import { motion } from "framer-motion";
import { BadgeCheck, Bot } from "lucide-react";

import { LogoMark } from "@/components/brand/Logo";
import { Skeleton } from "@/components/ui/Feedback";
import { useShowcase } from "@/lib/queries";

const appear = (delay: number) => ({
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { delay, duration: 0.55, ease: [0.22, 1, 0.36, 1] as const },
});

/** A real exchange: the question is answered by the assistant from the demo account's transactions. */
export function ExampleAnswer() {
  const { data, isPending, isError } = useShowcase();
  return (
    <div className="relative mx-auto w-full max-w-md">
      <div aria-hidden className="absolute -inset-8 rounded-[2.5rem] bg-grad-primary opacity-25 blur-3xl" />
      <div className="glass-strong sweep relative space-y-3 rounded-3xl p-4 sm:p-5">
        <div className="flex items-center gap-2 border-b border-[var(--glass-border)] pb-3 text-xs text-muted-foreground">
          <Bot className="size-4 text-violet-ink" /> FINJARVIS assistant · demo account
          <span className="ml-auto flex gap-1" aria-hidden>
            <span className="size-2 rounded-full bg-magenta/70" />
            <span className="size-2 rounded-full bg-violet/70" />
            <span className="size-2 rounded-full bg-cyan/70" />
          </span>
        </div>
        {isPending && (
          <div className="space-y-2" role="status" aria-label="Loading example">
            <Skeleton className="ml-auto h-8 w-2/3" />
            <Skeleton className="h-16 w-full" />
          </div>
        )}
        {isError && <p className="py-6 text-center text-sm text-muted-foreground">The example appears once the server is running.</p>}
        {data && (
          <>
            <motion.div
              {...appear(0.3)}
              className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-grad-primary px-3.5 py-2 text-sm text-white shadow-[0_8px_24px_-10px_rgba(124,92,255,0.8)]"
            >
              {data.assistant.question}
            </motion.div>
            <motion.div {...appear(0.9)} className="flex gap-2">
              <LogoMark className="size-7" />
              <div className="min-w-0 rounded-2xl rounded-tl-md border border-[var(--glass-border)] bg-[var(--glass)] p-3 text-sm">
                <p>{data.assistant.answer}</p>
              </div>
            </motion.div>
            <motion.div {...appear(1.5)} className="flex items-center gap-2 pl-9 text-xs">
              <span className="inline-flex items-center gap-1 rounded-full border border-success/30 bg-success/12 px-2 py-0.5 font-medium text-success">
                <BadgeCheck className="size-3.5" /> Calculated from your transactions
              </span>
            </motion.div>
          </>
        )}
      </div>
    </div>
  );
}
