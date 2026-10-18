import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { BadgeCheck, GitPullRequest, ShieldAlert } from "lucide-react";

import { LogoMark } from "@/components/brand/Logo";
import { Skeleton } from "@/components/ui/Feedback";
import { api } from "@/lib/api";
import { keys } from "@/lib/queries";
import type { PublicExample } from "@/lib/types";

const appear = (delay: number) => ({
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { delay, duration: 0.55, ease: [0.22, 1, 0.36, 1] as const },
});

/** A real finding from the built-in demo pull request (GET /public/example), shown as a review card. */
export function ExampleAnswer() {
  const q = useQuery({
    queryKey: keys.example,
    queryFn: async () => (await api.get<PublicExample>("/public/example")).data,
    retry: false,
    staleTime: Infinity,
  });
  const f = q.data?.finding;
  return (
    <div className="relative mx-auto w-full max-w-md">
      <div aria-hidden className="absolute -inset-8 rounded-[2.5rem] bg-grad-primary opacity-25 blur-3xl" />
      <div className="glass-strong sweep relative space-y-3 rounded-3xl p-4 sm:p-5">
        <div className="flex items-center gap-2 border-b border-[var(--glass-border)] pb-3 text-xs text-muted-foreground">
          <GitPullRequest className="size-4 text-violet-ink" /> Demo pull request · add user API
          <span className="ml-auto flex gap-1" aria-hidden>
            <span className="size-2 rounded-full bg-magenta/70" />
            <span className="size-2 rounded-full bg-violet/70" />
            <span className="size-2 rounded-full bg-cyan/70" />
          </span>
        </div>
        {q.isPending ? (
          <div className="space-y-3" role="status" aria-label="Loading example">
            <Skeleton className="h-9 w-3/4" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-6 w-1/2" />
          </div>
        ) : !f ? (
          <p className="py-6 text-center text-sm text-muted-foreground">The live example appears here once the API is running.</p>
        ) : (
          <>
            <motion.div {...appear(0.4)} className="flex items-center gap-2 rounded-2xl border border-danger/30 bg-danger/10 px-3 py-2 text-sm">
              <ShieldAlert className="size-4 shrink-0 text-danger" />
              <span className="min-w-0 truncate font-medium">{f.title}</span>
              <span className="ml-auto shrink-0 rounded-full bg-grad-danger px-2 py-0.5 text-[11px] font-semibold uppercase text-white">{f.severity}</span>
            </motion.div>
            <motion.pre
              {...appear(0.9)}
              className="scrollbar-thin overflow-x-auto rounded-xl border border-[var(--glass-border)] bg-muted p-3 font-mono text-xs leading-relaxed"
            >
              <span className="text-muted-foreground">{f.file}:{f.line}</span>
              {"\n"}
              {f.snippet.trim()}
            </motion.pre>
            <motion.div {...appear(1.4)} className="flex gap-2">
              <LogoMark className="size-7" />
              <div className="min-w-0 space-y-2 rounded-2xl rounded-tl-md border border-[var(--glass-border)] bg-[var(--glass)] p-3 text-sm">
                <p className="text-muted-foreground">{f.explanation}</p>
                <p>
                  <strong>Fix:</strong> {f.remediation}
                </p>
              </div>
            </motion.div>
            <motion.div {...appear(1.9)} className="flex flex-wrap items-center gap-2 pl-9 text-xs">
              {f.fix_verified && (
                <span className="inline-flex items-center gap-1 rounded-full border border-success/30 bg-success/12 px-2 py-0.5 font-medium text-success">
                  <BadgeCheck className="size-3.5" /> Patch verified by re-scan
                </span>
              )}
              {f.cwe && <span className="rounded-full border border-violet/30 bg-violet/12 px-2 py-0.5 font-medium text-violet-ink">{f.cwe}</span>}
            </motion.div>
          </>
        )}
      </div>
    </div>
  );
}
