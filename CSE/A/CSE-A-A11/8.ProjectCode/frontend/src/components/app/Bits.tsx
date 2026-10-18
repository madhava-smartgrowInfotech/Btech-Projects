import { motion } from "framer-motion";
import { CheckCircle2, Loader2, OctagonAlert, ShieldAlert, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/Feedback";
import { SEV_TONE, VERDICT_INFO } from "@/lib/domain";
import type { Severity, Verdict } from "@/lib/types";
import { cn } from "@/lib/utils";

export function SevBadge({ severity }: { severity: Severity }) {
  return <Badge tone={SEV_TONE[severity]} className="uppercase tracking-wide">{severity}</Badge>;
}

const verdictIcon = { danger: OctagonAlert, warning: ShieldAlert, success: ShieldCheck } as const;
const verdictTone = {
  danger: "border-danger/40 bg-danger/[0.08] text-danger",
  warning: "border-warning/40 bg-warning/[0.08] text-warning",
  success: "border-success/40 bg-success/[0.08] text-success",
} as const;

export function VerdictBanner({ verdict, summary }: { verdict: Verdict; summary: string }) {
  const v = VERDICT_INFO[verdict];
  const Icon = verdictIcon[v.tone];
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("flex items-start gap-4 rounded-2xl border p-4 sm:p-5", verdictTone[v.tone])}
      role="status"
    >
      <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-current/10">
        <Icon className="size-6" />
      </span>
      <div className="min-w-0">
        <div className="font-display text-xl font-semibold">{v.title}</div>
        <p className="mt-0.5 text-sm text-foreground/80">{summary}</p>
      </div>
    </motion.div>
  );
}

/** Live list of what each agent is doing while a job runs (polled from /jobs/{id}). */
export function AgentProgress({ messages, title = "Agents are working…" }: { messages: string[]; title?: string }) {
  return (
    <Card className="space-y-4 p-5" role="status" aria-live="polite">
      <div className="flex items-center gap-2 font-display font-semibold">
        <Loader2 className="size-4 animate-spin text-violet-ink" /> {title}
      </div>
      <ProgressBar value={0} indeterminate label="Review in progress" />
      <ul className="space-y-1.5 text-sm">
        {messages.length === 0 && <li className="text-muted-foreground">Starting…</li>}
        {messages.map((m, i) => {
          const last = i === messages.length - 1;
          return (
            <motion.li key={i} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} className="flex items-center gap-2">
              {last ? <Loader2 className="size-4 shrink-0 animate-spin text-violet-ink" /> : <CheckCircle2 className="size-4 shrink-0 text-success" />}
              <span className={last ? "text-foreground" : "text-muted-foreground"}>{m}</span>
            </motion.li>
          );
        })}
      </ul>
    </Card>
  );
}

/** Small label + value pair used in dense panels. */
export function Fact({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-0.5">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-sm font-medium">{children}</div>
    </div>
  );
}
