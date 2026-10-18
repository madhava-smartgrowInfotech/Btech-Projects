import { Check, Copy } from "lucide-react";
import { useState } from "react";

import { IconButton } from "@/components/ui/Button";
import { toast } from "@/components/ui/Toast";
import { cn } from "@/lib/utils";

/** Monospace block with a copy button. `diff` colours added / removed lines. */
export function CodeBlock({
  code,
  language,
  className,
  maxHeight = "20rem",
  label,
}: {
  code: string;
  language?: "diff" | "python" | string;
  className?: string;
  maxHeight?: string;
  label?: string;
}) {
  const [copied, setCopied] = useState(false);
  const lines = code.replace(/\n$/, "").split("\n");

  async function copy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      toast.error("Couldn't copy. Select the text and copy it manually.");
    }
  }

  return (
    <div className={cn("group relative overflow-hidden rounded-xl border border-[var(--glass-border)] bg-muted", className)}>
      {label && <div className="border-b border-[var(--glass-border)] px-3 py-1.5 text-xs text-muted-foreground">{label}</div>}
      <IconButton
        label={copied ? "Copied" : "Copy code"}
        size="icon-sm"
        onClick={copy}
        className="absolute right-1.5 top-1.5 z-10 bg-[var(--glass-strong)] opacity-0 transition-opacity focus-visible:opacity-100 group-hover:opacity-100 max-sm:opacity-100"
      >
        {copied ? <Check className="text-success" /> : <Copy />}
      </IconButton>
      <pre tabIndex={0} aria-label={label ?? "Code"} className="scrollbar-thin overflow-auto p-3 font-mono text-xs leading-relaxed" style={{ maxHeight }}>
        <code>
          {lines.map((line, i) => (
            <span
              key={i}
              className={cn(
                "block min-w-max px-1",
                language === "diff" && line.startsWith("+") && !line.startsWith("+++") && "bg-success/12 text-success",
                language === "diff" && line.startsWith("-") && !line.startsWith("---") && "bg-danger/12 text-danger",
                language === "diff" && line.startsWith("@@") && "text-cyan-ink",
                language === "diff" && (line.startsWith("+++") || line.startsWith("---")) && "text-muted-foreground",
              )}
            >
              {line || " "}
            </span>
          ))}
        </code>
      </pre>
    </div>
  );
}
