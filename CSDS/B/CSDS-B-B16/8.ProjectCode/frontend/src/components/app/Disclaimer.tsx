import { ShieldAlert } from "lucide-react";

import { cn } from "@/lib/utils";

export function Disclaimer({ className }: { className?: string }) {
  return (
    <div role="note" className={cn("glass-flat flex items-start gap-3 rounded-2xl px-4 py-3 text-xs text-muted-foreground", className)}>
      <ShieldAlert className="mt-0.5 size-4 shrink-0 text-warning" aria-hidden />
      <p>
        RetinaGuard is a clinical decision-support aid. Results must be reviewed by a qualified professional and are not a final
        diagnosis.
      </p>
    </div>
  );
}
