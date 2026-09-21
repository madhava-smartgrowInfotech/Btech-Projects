import { BadgeCheck, CircleAlert, CircleHelp } from "lucide-react";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { Faithfulness } from "@/lib/types";
import { cn } from "@/lib/utils";

const META = {
  well_supported: { label: "Well supported", tone: "text-success border-success/30 bg-success/10", bar: "bg-success", icon: BadgeCheck },
  partly_supported: {
    label: "Partly supported",
    tone: "text-warning-foreground dark:text-warning border-warning/40 bg-warning/15",
    bar: "bg-warning",
    icon: CircleAlert,
  },
  weakly_supported: { label: "Weakly supported", tone: "text-destructive border-destructive/30 bg-destructive/10", bar: "bg-destructive", icon: CircleAlert },
  not_applicable: { label: "Not scored", tone: "text-muted-foreground border-border bg-muted", bar: "bg-muted-foreground", icon: CircleHelp },
};

export function FaithfulnessBadge({ faithfulness, className }: { faithfulness: Faithfulness | null; className?: string }) {
  if (!faithfulness || faithfulness.score === null) return null;
  const meta = META[faithfulness.label] ?? META.not_applicable;
  const Icon = meta.icon;
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={cn("inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium", meta.tone, className)}
          aria-label={`Faithfulness ${Math.round(faithfulness.score)} out of 100: ${meta.label}. Show details`}
        >
          <Icon className="size-3.5" />
          Faithfulness {Math.round(faithfulness.score)}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-80 text-sm" align="start">
        <div className="mb-2 font-semibold">{meta.label}</div>
        <p className="mb-3 text-xs text-muted-foreground">
          Each statement in the answer was checked against the clause it cites by an independent language-inference model.
        </p>
        <ul className="max-h-64 space-y-2.5 overflow-auto pr-1">
          {faithfulness.claims.map((c, i) => (
            <li key={i} className="space-y-1">
              <div className="flex items-start justify-between gap-2 text-xs">
                <span className="leading-snug">{c.text}</span>
                <span className="shrink-0 font-semibold tabular-nums">{Math.round(c.support * 100)}%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                <div
                  className={cn("h-full rounded-full", c.support >= 0.8 ? "bg-success" : c.support >= 0.5 ? "bg-warning" : "bg-destructive")}
                  style={{ width: `${Math.max(4, c.support * 100)}%` }}
                />
              </div>
              {c.note && <div className="text-[11px] text-muted-foreground">{c.note}</div>}
            </li>
          ))}
        </ul>
      </PopoverContent>
    </Popover>
  );
}
