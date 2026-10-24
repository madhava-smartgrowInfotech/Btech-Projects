import { CheckCircle2, ShieldAlert } from "lucide-react";
import { Link } from "react-router";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { type ResultSummary, type Severity } from "@/lib/api";
import { SEVERITY_LABEL, SEVERITY_TONE, pct } from "@/lib/disease";
import { cn, formatDate } from "@/lib/utils";

export function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  return (
    <Badge tone={SEVERITY_TONE[severity]} className={className}>
      {severity === "none" ? <CheckCircle2 aria-hidden /> : <ShieldAlert aria-hidden />}
      {SEVERITY_LABEL[severity]}
    </Badge>
  );
}

/** Horizontal meter; the number is always printed next to it so colour is never the only signal. */
export function Meter({ value, className, tone = "primary" }: { value: number; className?: string; tone?: "primary" | "muted" }) {
  const w = Math.max(2, Math.min(100, value * 100));
  return (
    <div className={cn("h-2 w-full overflow-hidden rounded-full bg-muted", className)} role="presentation">
      <div className={cn("h-full rounded-full", tone === "primary" ? "bg-grad-primary" : "bg-muted-foreground/50")} style={{ width: `${w}%` }} />
    </div>
  );
}

/** A past detection: leaf photo, diagnosis, severity, confidence, date. Links to the result page. */
export function ResultCard({ r, footer }: { r: ResultSummary; footer?: React.ReactNode }) {
  return (
    <Card interactive className="flex h-full flex-col overflow-hidden">
      <Link to={`/result/${r.result_id}`} className="block focus-visible:outline-offset-[-2px]" aria-label={`Open result: ${r.predicted_disease}`}>
        <img src={r.image_url} alt={`Leaf scanned on ${formatDate(r.detection_date)}`} loading="lazy" className="h-40 w-full object-cover" />
      </Link>
      <div className="flex flex-1 flex-col gap-2 p-4">
        <Link to={`/result/${r.result_id}`} className="font-display text-sm font-semibold leading-snug hover:text-violet-ink">
          {r.predicted_disease}
        </Link>
        <div className="mt-auto flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <SeverityBadge severity={r.severity} />
          <span className="tabular-nums">{pct(r.confidence)}</span>
          <span className="ml-auto">{formatDate(r.detection_date, true)}</span>
        </div>
        {footer}
      </div>
    </Card>
  );
}
