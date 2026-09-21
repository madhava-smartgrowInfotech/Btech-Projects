import { Check, Loader2 } from "lucide-react";

import { Progress } from "@/components/ui/progress";
import type { DocStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const STEPS: { key: DocStatus; label: string }[] = [
  { key: "parsing", label: "Read PDF & split into clauses" },
  { key: "indexing", label: "Build keyword + semantic index" },
  { key: "extracting", label: "Policy Card & risk highlights" },
  { key: "ready", label: "Ready" },
];
const ORDER: DocStatus[] = ["queued", "parsing", "indexing", "extracting", "ready"];

export function ProcessingSteps({ status, progress, detail }: { status: DocStatus; progress: number; detail?: string | null }) {
  const current = ORDER.indexOf(status);
  return (
    <div className="space-y-3" aria-live="polite">
      <Progress value={progress} aria-label="Processing progress" />
      <ol className="grid gap-2 sm:grid-cols-4">
        {STEPS.map((step) => {
          const idx = ORDER.indexOf(step.key);
          const done = current > idx || status === "ready";
          const active = current === idx && status !== "ready";
          return (
            <li
              key={step.key}
              className={cn(
                "flex items-center gap-2 rounded-lg border px-3 py-2 text-xs",
                done && "border-success/30 bg-success/5 text-foreground",
                active && "border-primary/40 bg-primary/5 font-medium",
                !done && !active && "text-muted-foreground",
              )}
            >
              {done ? (
                <Check className="size-3.5 text-success" />
              ) : active ? (
                <Loader2 className="size-3.5 animate-spin text-primary" />
              ) : (
                <span className="size-3.5 rounded-full border" />
              )}
              {step.label}
            </li>
          );
        })}
      </ol>
      {detail && <p className="text-xs text-muted-foreground">{detail}…</p>}
    </div>
  );
}
