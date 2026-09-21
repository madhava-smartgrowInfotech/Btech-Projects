import { Bot, Scale, ShieldCheck } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";

import { SeverityBadge } from "@/components/common/Badges";
import { EmptyState } from "@/components/common/States";
import { SourceChip } from "@/components/policy/SourceChip";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Risk, Severity } from "@/lib/types";
import { cn } from "@/lib/utils";

const accent: Record<Severity, string> = {
  high: "before:bg-destructive",
  medium: "before:bg-warning",
  low: "before:bg-info",
};

export function RiskList({ risks, onOpenSource }: { risks: Risk[]; onOpenSource: (page: number, ordinal: number | null) => void }) {
  const [filter, setFilter] = useState<Severity | "all">("all");
  const counts = { high: 0, medium: 0, low: 0 } as Record<Severity, number>;
  risks.forEach((r) => (counts[r.severity] += 1));
  const shown = filter === "all" ? risks : risks.filter((r) => r.severity === filter);

  if (!risks.length) {
    return (
      <EmptyState icon={<ShieldCheck />} title="No risk highlights" description="Nothing in this policy was flagged as a cost or claim trap." />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by severity">
        {(["all", "high", "medium", "low"] as const).map((key) => (
          <Button
            key={key}
            size="sm"
            variant={filter === key ? "default" : "outline"}
            onClick={() => setFilter(key)}
            aria-pressed={filter === key}
            className="capitalize"
          >
            {key} {key === "all" ? risks.length : counts[key]}
          </Button>
        ))}
      </div>
      <ul className="space-y-3">
        {shown.map((r, i) => (
          <motion.li
            key={r.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: Math.min(i * 0.04, 0.3) }}
            className={cn(
              "relative overflow-hidden rounded-xl border bg-card p-4 pl-5 before:absolute before:inset-y-0 before:left-0 before:w-1",
              accent[r.severity],
            )}
          >
            <div className="flex flex-wrap items-center gap-2">
              <SeverityBadge severity={r.severity} />
              <Badge variant="outline" className="gap-1 text-[11px] font-normal text-muted-foreground">
                {r.source === "rule" ? <Scale className="size-3" /> : <Bot className="size-3" />}
                {r.source === "rule" ? "Rule check" : "AI finding"}
              </Badge>
              <span className="text-[11px] capitalize text-muted-foreground">{r.category.replace("_", " ")}</span>
            </div>
            <h3 className="mt-2 font-semibold leading-snug">{r.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">{r.explanation}</p>
            {r.quote && <blockquote className="mt-2 border-l-2 pl-3 text-xs italic text-muted-foreground">“{r.quote}”</blockquote>}
            {r.page && (
              <SourceChip
                label={r.clause_label}
                page={r.page}
                onOpen={() => onOpenSource(r.page!, r.clause_ordinal)}
                className="mt-2"
              />
            )}
          </motion.li>
        ))}
      </ul>
    </div>
  );
}
