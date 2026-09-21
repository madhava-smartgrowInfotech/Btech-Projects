import { Fragment, type ReactNode } from "react";

import type { Citation } from "@/lib/types";

/** Minimal, safe Markdown for answers: paragraphs, bullet/numbered lists, **bold**, and [C12] citation tags. */
export function AnswerMarkdown({
  text,
  citations,
  onCite,
}: {
  text: string;
  citations: Citation[];
  onCite: (citation: Citation) => void;
}) {
  const byOrdinal = new Map(citations.map((c) => [c.ordinal, c]));
  const numberOf = new Map(citations.map((c, i) => [c.ordinal, i + 1]));

  function inline(line: string, key: string): ReactNode[] {
    const parts = line.split(/(\*\*[^*]+\*\*|\[C\d+\])/g).filter(Boolean);
    return parts.map((part, i) => {
      const k = `${key}-${i}`;
      const cite = part.match(/^\[C(\d+)\]$/);
      if (cite) {
        const c = byOrdinal.get(Number(cite[1]));
        if (!c) return null;
        return (
          <button
            key={k}
            type="button"
            onClick={() => onCite(c)}
            className="mx-0.5 inline-flex h-5 min-w-5 -translate-y-px items-center justify-center rounded-md bg-primary/10 px-1 align-middle text-[11px] font-semibold text-primary transition-colors hover:bg-primary hover:text-primary-foreground"
            aria-label={`Source ${numberOf.get(c.ordinal)}: ${c.label}, page ${c.page}`}
            title={`${c.label} · page ${c.page}`}
          >
            {numberOf.get(c.ordinal)}
          </button>
        );
      }
      if (part.startsWith("**") && part.endsWith("**")) return <strong key={k}>{part.slice(2, -2)}</strong>;
      return <Fragment key={k}>{part}</Fragment>;
    });
  }

  const blocks: ReactNode[] = [];
  const lines = text.replace(/\r/g, "").split("\n");
  let list: { ordered: boolean; items: string[] } | null = null;
  const flush = () => {
    if (!list) return;
    const Tag = list.ordered ? "ol" : "ul";
    const idx = blocks.length;
    blocks.push(
      <Tag key={`l${idx}`}>
        {list.items.map((item, i) => (
          <li key={i}>{inline(item, `l${idx}-${i}`)}</li>
        ))}
      </Tag>,
    );
    list = null;
  };
  lines.forEach((raw, i) => {
    const line = raw.trim();
    const bullet = line.match(/^[-*•]\s+(.*)$/);
    const numbered = line.match(/^\d+[.)]\s+(.*)$/);
    if (bullet || numbered) {
      const ordered = Boolean(numbered);
      if (!list || list.ordered !== ordered) {
        flush();
        list = { ordered, items: [] };
      }
      list.items.push((bullet ?? numbered)![1]);
      return;
    }
    flush();
    if (!line) return;
    const heading = line.match(/^#{1,4}\s+(.*)$/);
    blocks.push(
      heading ? (
        <p key={`h${i}`} className="font-semibold">
          {inline(heading[1], `h${i}`)}
        </p>
      ) : (
        <p key={`p${i}`}>{inline(line, `p${i}`)}</p>
      ),
    );
  });
  flush();
  return <div className="prose-answer text-sm leading-relaxed">{blocks}</div>;
}
