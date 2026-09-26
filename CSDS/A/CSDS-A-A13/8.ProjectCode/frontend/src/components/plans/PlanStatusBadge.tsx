import { Archive, CircleDashed, Globe } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { PlanStatus } from "@/lib/types";

export function PlanStatusBadge({ status, version }: { status: PlanStatus | null; version?: number }) {
  const v = version ? ` v${version}` : "";
  if (status === "published")
    return (
      <Badge variant="success">
        <Globe /> Published{v}
      </Badge>
    );
  if (status === "draft")
    return (
      <Badge variant="default">
        <CircleDashed /> Draft{v}
      </Badge>
    );
  if (status === "archived")
    return (
      <Badge variant="secondary">
        <Archive /> Replaced{v}
      </Badge>
    );
  return <Badge variant="outline">No plan yet</Badge>;
}
