import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, Bot, ChevronDown, ShieldCheck, TriangleAlert } from "lucide-react";
import { useId, useState } from "react";

import { CodeBlock } from "@/components/app/CodeBlock";
import { SevBadge } from "@/components/app/Bits";
import { Badge } from "@/components/ui/Badge";
import type { Finding } from "@/lib/types";
import { cn } from "@/lib/utils";

const DETECTOR: Record<string, string> = { static: "AST/taint", regex: "pattern", ml: "ML model" };

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{title}</h4>
      <div className="text-sm leading-relaxed">{children}</div>
    </div>
  );
}

/** One finding: header row always visible, details (code, flow, impact, fix, verified patch) expand in place. */
export function FindingCard({ f, defaultOpen = false }: { f: Finding; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  const panel = useId();
  const showExploit = f.exploit && f.exploit !== "n/a" && f.exploit !== "n/a (latent)";
  const lang = f.file.endsWith(".py") ? "python" : undefined;
  return (
    <div className="glass rounded-2xl">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panel}
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-start gap-3 rounded-2xl p-4 text-left"
      >
        <SevBadge severity={f.severity} />
        <span className="min-w-0 flex-1">
          <span className="block font-medium">{f.title}</span>
          <span className="block truncate font-mono text-xs text-muted-foreground">
            {f.file}:{f.line}
            {!f.in_diff && " · pre-existing"}
          </span>
        </span>
        {f.cwe && <Badge tone="violet" className="hidden sm:inline-flex">{f.cwe}</Badge>}
        <ChevronDown className={cn("mt-1 size-4 shrink-0 text-muted-foreground transition-transform", open && "rotate-180")} />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            id={panel}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="space-y-4 border-t border-[var(--glass-border)] p-4">
              <div className="flex flex-wrap gap-1.5">
                <Badge tone="neutral">{f.confidence} confidence</Badge>
                {f.cwe && <Badge tone="violet">{f.cwe}</Badge>}
                {f.owasp && <Badge tone="neutral">{f.owasp}</Badge>}
                {f.function && <Badge tone="neutral">in {f.function}()</Badge>}
                <Badge tone="neutral">{DETECTOR[f.detector] ?? "rule"}</Badge>
                {f.ml !== null && f.ml >= 0.5 && <Badge tone="warning">ML risk {Math.round(f.ml * 100)}%</Badge>}
                {!f.in_diff && <Badge tone="neutral">pre-existing</Badge>}
              </div>
              {f.snippet && <CodeBlock code={f.snippet} language={lang} maxHeight="10rem" label={`${f.file}:${f.line}`} />}
              <Section title="What is wrong">
                {f.explanation}
                {f.llm && <span className="ml-2 text-xs text-muted-foreground">(written by the LLM agent)</span>}
              </Section>
              {f.flow.length > 0 && (
                <Section title="Data flow">
                  <ol className="flex flex-wrap items-center gap-1.5">
                    {f.flow.map((step, i) => (
                      <li key={i} className="flex items-center gap-1.5">
                        <span className="rounded-lg border border-[var(--glass-border)] bg-muted px-2 py-1 text-xs">{step}</span>
                        {i < f.flow.length - 1 && <ArrowRight className="size-3.5 text-violet-ink" aria-hidden />}
                      </li>
                    ))}
                  </ol>
                </Section>
              )}
              {f.impact && <Section title="Impact">{f.impact}</Section>}
              {showExploit && (
                <Section title="Example attack">
                  <code className="break-words rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{f.exploit}</code>
                </Section>
              )}
              {f.corroboration && (
                <div className="flex items-start gap-2 rounded-xl border border-info/30 bg-info/10 p-3 text-sm">
                  <Bot className="mt-0.5 size-4 shrink-0 text-info" /> {f.corroboration}
                </div>
              )}
              <Section title="How to fix">{f.remediation}</Section>
              {f.patch ? (
                <Section title="Suggested patch">
                  <div className="space-y-2">
                    {f.fix_verified ? (
                      <Badge tone="success"><ShieldCheck /> verified: re-scan clean</Badge>
                    ) : (
                      <Badge tone="warning"><TriangleAlert /> review manually</Badge>
                    )}
                    <CodeBlock code={f.patch} language="diff" maxHeight="14rem" />
                    {f.fix_note && <p className="text-xs text-muted-foreground">{f.fix_note}</p>}
                  </div>
                </Section>
              ) : (
                f.safe_example && (
                  <Section title="Safe pattern">
                    <CodeBlock code={f.safe_example} language={lang} maxHeight="8rem" />
                  </Section>
                )
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
