import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import remarkGfm from "remark-gfm";

import { CodeBlock } from "@/components/app/CodeBlock";
import { cn } from "@/lib/utils";

// The PR-comment export contains <details>/<summary>/<code>; everything else raw is stripped.
const schema = {
  ...defaultSchema,
  tagNames: [...(defaultSchema.tagNames ?? []), "details", "summary"],
  attributes: { ...defaultSchema.attributes, "*": [...(defaultSchema.attributes?.["*"] ?? []), "className"] },
};

/** Renders assistant / report markdown safely (raw HTML is sanitised). Fenced code uses the shared CodeBlock. */
export default function Markdown({ children, className }: { children: string; className?: string }) {
  return (
    <div className={cn("prose-answer text-sm leading-relaxed", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, [rehypeSanitize, schema]]}
        components={{
          pre: ({ children: c }) => <>{c}</>,
          code: ({ className: cls, children: c }) => {
            const text = String(c ?? "");
            const lang = /language-(\w+)/.exec(cls ?? "")?.[1];
            if (lang || text.includes("\n")) return <CodeBlock code={text} language={lang} maxHeight="18rem" className="my-2" />;
            return <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]">{c}</code>;
          },
          a: ({ href, children: c }) => (
            <a href={href} target="_blank" rel="noreferrer noopener" className="text-violet-ink underline underline-offset-2">
              {c}
            </a>
          ),
          table: ({ children: c }) => (
            <div className="scrollbar-thin my-2 overflow-x-auto rounded-xl border border-[var(--glass-border)]">
              <table className="w-full text-sm">{c}</table>
            </div>
          ),
          th: ({ children: c }) => <th className="border-b border-[var(--glass-border)] px-3 py-2 text-left text-xs font-medium text-muted-foreground">{c}</th>,
          td: ({ children: c }) => <td className="border-b border-[var(--glass-border)] px-3 py-2 last:border-0">{c}</td>,
          h2: ({ children: c }) => <h2 className="mb-2 mt-3 font-display text-lg font-semibold">{c}</h2>,
          h3: ({ children: c }) => <h3 className="mb-1.5 mt-3 font-display text-base font-semibold">{c}</h3>,
          details: ({ children: c }) => <details className="my-2 rounded-xl border border-[var(--glass-border)] bg-muted px-3 py-2">{c}</details>,
          summary: ({ children: c }) => <summary className="cursor-pointer font-medium">{c}</summary>,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
