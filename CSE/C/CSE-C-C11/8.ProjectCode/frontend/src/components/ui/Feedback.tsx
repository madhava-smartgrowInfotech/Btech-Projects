import { motion } from "framer-motion";
import { AlertTriangle, Loader2, RefreshCw } from "lucide-react";
import type { ReactNode } from "react";

import { LogoMark } from "@/components/brand/Logo";
import { Button } from "@/components/ui/Button";
import { errorMessage } from "@/lib/api";
import { cn } from "@/lib/utils";

export function ProgressBar({
  value,
  className,
  label,
  indeterminate,
}: {
  value: number;
  className?: string;
  label?: string;
  indeterminate?: boolean;
}) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={indeterminate ? undefined : Math.round(pct)}
      className={cn("relative h-1.5 w-full overflow-hidden rounded-full bg-muted", className)}
    >
      <motion.div
        className="absolute inset-y-0 left-0 rounded-full bg-grad-primary shadow-[0_0_12px_rgba(34,211,238,0.6)]"
        initial={false}
        animate={{ width: indeterminate ? "40%" : `${pct}%`, x: indeterminate ? ["-100%", "250%"] : 0 }}
        transition={indeterminate ? { duration: 1.4, repeat: Infinity, ease: "easeInOut" } : { duration: 0.5, ease: "easeOut" }}
      />
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden className={cn("skeleton rounded-lg", className)} />;
}

export function CardsSkeleton({ count = 3, className }: { count?: number; className?: string }) {
  return (
    <div className={cn("grid gap-4 sm:grid-cols-2 lg:grid-cols-3", className)} role="status" aria-label="Loading">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="glass space-y-3 rounded-2xl p-5">
          <Skeleton className="h-5 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-20 w-full" />
        </div>
      ))}
    </div>
  );
}

export function FullPageLoader() {
  return (
    <div className="grid min-h-dvh place-items-center" role="status" aria-live="polite">
      <div className="flex flex-col items-center gap-4 text-muted-foreground">
        <div className="relative">
          <div className="absolute inset-0 -m-3 animate-pulse rounded-full bg-grad-primary opacity-30 blur-xl" />
          <LogoMark className="relative size-12" />
        </div>
        <span className="text-sm">Loading FINJARVIS…</span>
      </div>
    </div>
  );
}

export function InlineLoader({ label = "Loading…", className }: { label?: string; className?: string }) {
  return (
    <div className={cn("flex items-center gap-2 text-sm text-muted-foreground", className)} role="status">
      <Loader2 className="size-4 animate-spin text-violet-ink" />
      {label}
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: {
  icon: ReactNode;
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className={cn(
        "relative flex flex-col items-center justify-center gap-4 overflow-hidden rounded-2xl border border-dashed border-[var(--glass-border)] bg-[var(--glass)] px-6 py-12 text-center",
        className,
      )}
    >
      <div className="pointer-events-none absolute left-1/2 top-0 h-32 w-64 -translate-x-1/2 rounded-full bg-violet/20 blur-3xl" />
      <div className="relative grid size-14 place-items-center rounded-2xl bg-grad-soft text-violet-ink ring-1 ring-[var(--glass-border)] [&_svg]:size-6">
        {icon}
      </div>
      <div className="relative space-y-1.5">
        <h3 className="font-display text-lg font-semibold">{title}</h3>
        {description && <p className="mx-auto max-w-md text-sm text-muted-foreground">{description}</p>}
      </div>
      {action && <div className="relative flex flex-wrap justify-center gap-2">{action}</div>}
    </motion.div>
  );
}

/** Says what failed (the API's own message) and what to do (retry / hint). */
export function ErrorState({
  error,
  title = "Couldn't load this",
  hint,
  onRetry,
  className,
}: {
  error: unknown;
  title?: string;
  hint?: ReactNode;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-center gap-3 rounded-2xl border border-danger/30 bg-danger/[0.06] px-6 py-10 text-center",
        className,
      )}
    >
      <div className="grid size-12 place-items-center rounded-2xl bg-danger/12 text-danger">
        <AlertTriangle className="size-6" />
      </div>
      <div className="space-y-1">
        <h3 className="font-display font-semibold">{title}</h3>
        <p className="text-sm text-muted-foreground">{errorMessage(error)}</p>
        {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
      </div>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          <RefreshCw /> Try again
        </Button>
      )}
    </div>
  );
}
