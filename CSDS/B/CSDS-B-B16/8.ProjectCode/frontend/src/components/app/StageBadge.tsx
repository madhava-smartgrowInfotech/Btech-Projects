import { Badge } from "@/components/ui/Badge";
import { STAGE_TONE } from "@/lib/retina";
import type { Stage } from "@/lib/types";

export function StageBadge({ stage }: { stage: Stage | null | undefined }) {
  if (!stage) return <Badge tone="neutral">Pending</Badge>;
  return <Badge tone={STAGE_TONE[stage]}>{stage}</Badge>;
}
