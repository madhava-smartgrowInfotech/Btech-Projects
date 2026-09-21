import { BadgeCheck, FileSearch, TriangleAlert } from "lucide-react";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

/** "Clause 4.2 · p. 5" - opens the page with the clause highlighted. */
export function SourceChip({
  label,
  page,
  verified,
  quote,
  onOpen,
  className,
}: {
  label?: string | null;
  page: number | null;
  verified?: boolean;
  quote?: string | null;
  onOpen?: () => void;
  className?: string;
}) {
  if (!page) return null;
  const short = label ? label.split(" - ")[0] : "Source";
  const chip = (
    <button
      type="button"
      onClick={onOpen}
      disabled={!onOpen}
      className={cn(
        "inline-flex max-w-full items-center gap-1 rounded-md border bg-background px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground transition-colors enabled:hover:border-primary/50 enabled:hover:text-primary",
        className,
      )}
    >
      {verified === false ? (
        <TriangleAlert className="size-3 shrink-0 text-warning" aria-label="Quote not verified" />
      ) : verified ? (
        <BadgeCheck className="size-3 shrink-0 text-success" aria-label="Verified in the text" />
      ) : (
        <FileSearch className="size-3 shrink-0" />
      )}
      <span className="truncate">
        {short} · p. {page}
      </span>
    </button>
  );
  if (!quote && verified === undefined) return chip;
  return (
    <Tooltip>
      <TooltipTrigger asChild>{chip}</TooltipTrigger>
      <TooltipContent className="max-w-xs text-xs">
        {quote && <p className="mb-1 italic">“{quote}”</p>}
        <p className="opacity-80">
          {verified === false
            ? "This quote could not be matched word-for-word in the policy text - check the page."
            : "Found in the policy text. Click to open the page."}
        </p>
      </TooltipContent>
    </Tooltip>
  );
}
