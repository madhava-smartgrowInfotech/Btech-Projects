import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useI18n } from "@/lib/i18n";
import type { Highlight } from "@/lib/types";
import { cn } from "@/lib/utils";

/** Shows a message with its risky phrases marked; hover/tap a mark to see why it was flagged. */
export function HighlightedText({ text, highlights, className }: { text: string; highlights: Highlight[]; className?: string }) {
  const { tx, t } = useI18n();
  const parts: React.ReactNode[] = [];
  let cursor = 0;
  [...highlights]
    .sort((a, b) => a.start - b.start)
    .forEach((h, i) => {
      if (h.start < cursor) return;
      if (h.start > cursor) parts.push(<span key={`t${i}`}>{text.slice(cursor, h.start)}</span>);
      const why = h.rules.length ? h.rules.map((r) => tx(`rule.${r}`, r)).join(" · ") : t("sms.model_flagged");
      parts.push(
        <Tooltip key={`h${i}`}>
          <TooltipTrigger asChild>
            <mark
              tabIndex={0}
              className={cn(
                "cursor-help rounded px-0.5 text-inherit underline decoration-2 underline-offset-2",
                h.sources.includes("rule") ? "bg-danger/15 decoration-danger" : "bg-caution/20 decoration-caution",
              )}
            >
              {text.slice(h.start, h.end)}
            </mark>
          </TooltipTrigger>
          <TooltipContent className="max-w-xs">{why}</TooltipContent>
        </Tooltip>,
      );
      cursor = h.end;
    });
  if (cursor < text.length) parts.push(<span key="end">{text.slice(cursor)}</span>);
  return <p className={cn("whitespace-pre-wrap break-words leading-relaxed", className)}>{parts}</p>;
}
