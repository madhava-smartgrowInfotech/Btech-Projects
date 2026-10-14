import type { ReactNode } from "react";

/** Bold segments (**text**) inside one line. Text is rendered as React nodes, so nothing is injected as HTML. */
function inline(line: string): ReactNode[] {
  return line.split(/(\*\*[^*]+\*\*)/).map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? <strong key={i}>{part.slice(2, -2)}</strong> : <span key={i}>{part}</span>,
  );
}

/**
 * Renders the assistant's answer: headings, bullet lists, bold and paragraphs. Only these forms
 * are supported on purpose; anything else shows as plain text.
 */
export function Markdown({ text }: { text: string }) {
  const out: ReactNode[] = [];
  let list: string[] | null = null;

  const flush = () => {
    if (!list) return;
    const items = list;
    out.push(
      <ul key={out.length} className="list-disc space-y-1 pl-5">
        {items.map((item, i) => (
          <li key={i}>{inline(item)}</li>
        ))}
      </ul>,
    );
    list = null;
  };

  for (const raw of text.split("\n")) {
    const line = raw.trimEnd();
    const bullet = /^\s*[-*]\s+(.*)$/.exec(line);
    if (bullet) {
      list = [...(list ?? []), bullet[1]];
      continue;
    }
    flush();
    const heading = /^#{1,4}\s+(.*)$/.exec(line);
    if (heading) out.push(<p key={out.length} className="pt-1 font-display font-semibold">{inline(heading[1])}</p>);
    else if (line.trim()) out.push(<p key={out.length}>{inline(line)}</p>);
  }
  flush();

  return <div className="space-y-2">{out}</div>;
}
