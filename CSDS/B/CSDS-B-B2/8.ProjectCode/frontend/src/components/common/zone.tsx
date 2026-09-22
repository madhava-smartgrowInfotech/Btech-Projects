import { CircleCheck, CircleX, TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import { ZONE_COLOR, type ZoneLabel } from "@/lib/zones";

const ICON = { Strong: CircleCheck, Weak: TriangleAlert, Dead: CircleX } as const;

/** Zone class with icon + text - colour never carries the meaning alone. */
export function ZoneBadge({ label, confidence, className }: { label: ZoneLabel | null | undefined; confidence?: number | null; className?: string }) {
  if (!label) return <span className={cn("text-xs text-muted-foreground", className)}>Not classified</span>;
  const Icon = ICON[label];
  return (
    <span
      className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold", className)}
      style={{ backgroundColor: `${ZONE_COLOR[label]}1f`, color: label === "Weak" ? "#8a5a00" : ZONE_COLOR[label] }}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden />
      {label}
      {confidence != null && <span className="font-normal opacity-80">· {Math.round(confidence * 100)}%</span>}
    </span>
  );
}

/** Stacked share of Strong / Weak / Dead readings with a 2px gap between segments. */
export function ZoneBar({ strong, weak, dead, className }: { strong: number; weak: number; dead: number; className?: string }) {
  const total = Math.max(strong + weak + dead, 1);
  const parts: [ZoneLabel, number][] = [["Strong", strong], ["Weak", weak], ["Dead", dead]];
  return (
    <div className={className}>
      <div className="flex h-2.5 w-full gap-[2px] overflow-hidden rounded-full" role="img" aria-label={`${strong} strong, ${weak} weak, ${dead} dead readings`}>
        {parts.filter(([, n]) => n > 0).map(([label, n]) => (
          <span key={label} className="h-full first:rounded-l-full last:rounded-r-full" style={{ width: `${(n / total) * 100}%`, backgroundColor: ZONE_COLOR[label] }} />
        ))}
      </div>
      <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
        {parts.map(([label, n]) => (
          <span key={label} className="inline-flex items-center gap-1 tabular">
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: ZONE_COLOR[label] }} aria-hidden />
            {label} {Math.round((n / total) * 100)}%
          </span>
        ))}
      </div>
    </div>
  );
}
