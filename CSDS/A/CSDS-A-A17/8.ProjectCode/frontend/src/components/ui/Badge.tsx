import type { HTMLAttributes } from "react";
import { cn } from "@/lib/format";

type Tone = "brand" | "amber" | "rose" | "slate" | "sky";

const toneClasses: Record<Tone, string> = {
  brand: "bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-200",
  amber: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200",
  rose: "bg-rose-50 text-rose-700 ring-1 ring-inset ring-rose-200",
  slate: "bg-ink-100 text-ink-600 ring-1 ring-inset ring-ink-200",
  sky: "bg-sky-50 text-sky-700 ring-1 ring-inset ring-sky-200",
};

export function Badge({
  className,
  tone = "slate",
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        toneClasses[tone],
        className
      )}
      {...props}
    />
  );
}

const GRADE_TONE: Record<string, Tone> = { A: "brand", B: "sky", C: "amber", Reject: "rose" };

export function GradeBadge({ grade }: { grade: string }) {
  return (
    <Badge tone={GRADE_TONE[grade] ?? "slate"} className="text-sm font-semibold px-3 py-1">
      Grade {grade}
    </Badge>
  );
}
