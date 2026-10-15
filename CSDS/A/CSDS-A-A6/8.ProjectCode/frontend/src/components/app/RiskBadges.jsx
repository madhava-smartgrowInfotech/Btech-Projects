import { Badge } from "@/components/ui/Badge";
import { gradeTone, humanize, severityTone } from "@/lib/format.js";

export function GradeBadge({ grade }) {
  return (
    <Badge tone={gradeTone(grade)} className="px-3 py-1 font-display text-base font-semibold" aria-label={`Complexity grade ${grade || "unknown"}`}>
      {grade || "-"}
    </Badge>
  );
}

export function SeverityBadge({ severity }) {
  return <Badge tone={severityTone(severity)} className="whitespace-nowrap capitalize">{severity || "none"}</Badge>;
}

export { humanize };
