import { Badge } from "@/components/ui/Badge";
import type { Label } from "@/lib/api";
import { VERDICT } from "@/lib/verdict";
import { cn } from "@/lib/utils";

/** Verdict as icon + words + tone, so it never depends on color alone. */
export function VerdictBadge({ label, size = "md", className }: { label: Label; size?: "md" | "lg"; className?: string }) {
  const v = VERDICT[label];
  const Icon = v.icon;
  return (
    <Badge tone={v.tone} className={cn(size === "lg" && "gap-2 px-4 py-1.5 text-base font-semibold [&_svg]:size-5", className)}>
      <Icon aria-hidden />
      {label}
    </Badge>
  );
}
