import { motion } from "framer-motion";
import { BadgeCheck, Ban, Hospital, Stethoscope } from "lucide-react";

import { LogoMark } from "@/components/brand/Logo";

const appear = (delay: number) => ({
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { delay, duration: 0.55, ease: [0.22, 1, 0.36, 1] as const },
});

/** A consent check, step by step. Describes the flow; it shows no patient data. */
export function ExampleAnswer() {
  return (
    <div className="relative mx-auto w-full max-w-md">
      <div aria-hidden className="absolute -inset-8 rounded-[2.5rem] bg-grad-primary opacity-25 blur-3xl" />
      <div className="glass-strong sweep relative space-y-3 rounded-3xl p-4 sm:p-5">
        <div className="flex items-center gap-2 border-b border-[var(--glass-border)] pb-3 text-xs text-muted-foreground">
          <Hospital className="size-4 text-violet-ink" /> Consent check · Riverside Medical Center
          <span className="ml-auto flex gap-1" aria-hidden>
            <span className="size-2 rounded-full bg-magenta/70" />
            <span className="size-2 rounded-full bg-violet/70" />
            <span className="size-2 rounded-full bg-cyan/70" />
          </span>
        </div>
        <motion.div
          {...appear(0.6)}
          className="ml-auto flex w-fit max-w-[88%] items-start gap-2 rounded-2xl rounded-br-md bg-grad-primary px-3.5 py-2 text-sm text-white shadow-[0_8px_24px_-10px_rgba(124,92,255,0.8)]"
        >
          <Stethoscope className="mt-0.5 size-4 shrink-0" />
          <span>A doctor asks for this patient's history: "Cardiology referral".</span>
        </motion.div>
        <motion.div {...appear(1.3)} className="flex gap-2">
          <LogoMark className="size-7" />
          <div className="min-w-0 space-y-2 rounded-2xl rounded-tl-md border border-[var(--glass-border)] bg-[var(--glass)] p-3 text-sm">
            <p>
              <strong>Blocked.</strong> The patient has not granted this hospital access yet. The request waits in the patient's
              consent screen.
            </p>
            <div className="flex items-center gap-1.5 rounded-lg border border-[var(--glass-border)] bg-muted px-2 py-1.5 text-xs text-muted-foreground">
              <Ban className="size-3.5 shrink-0 text-warning" />
              <span className="truncate">Logged to the audit ledger as access.denied</span>
            </div>
          </div>
        </motion.div>
        <motion.div {...appear(2)} className="flex items-center gap-2 pl-9 text-xs">
          <span className="inline-flex items-center gap-1 rounded-full border border-success/30 bg-success/12 px-2 py-0.5 font-medium text-success">
            <BadgeCheck className="size-3.5" /> After the patient grants access, the records from every hospital merge into one timeline
          </span>
        </motion.div>
      </div>
    </div>
  );
}
