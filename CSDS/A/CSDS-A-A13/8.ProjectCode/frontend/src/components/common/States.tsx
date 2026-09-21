import type { ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { errorMessage } from "@/lib/api";
import { cn } from "@/lib/utils";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: {
  icon: LucideIcon;
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center rounded-xl border border-dashed px-6 py-12 text-center", className)}>
      <div className="mb-4 flex size-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
        <Icon className="size-6" aria-hidden />
      </div>
      <h3 className="text-base font-semibold">{title}</h3>
      {description && <p className="mt-1.5 max-w-md text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-5 flex flex-wrap justify-center gap-2">{action}</div>}
    </div>
  );
}

export function ErrorState({
  error,
  onRetry,
  title = "This could not be loaded",
  className,
}: {
  error: unknown;
  onRetry?: () => void;
  title?: string;
  className?: string;
}) {
  return (
    <div
      role="alert"
      className={cn("flex flex-col items-center justify-center rounded-xl border border-destructive/30 bg-destructive/5 px-6 py-10 text-center", className)}
    >
      <AlertTriangle className="mb-3 size-7 text-destructive" aria-hidden />
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-1 max-w-md text-sm text-muted-foreground">{errorMessage(error)}</p>
      {onRetry && (
        <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>
          <RefreshCw /> Try again
        </Button>
      )}
    </div>
  );
}

export function CardsSkeleton({ count = 4, className }: { count?: number; className?: string }) {
  return (
    <div className={cn("grid gap-4 sm:grid-cols-2 xl:grid-cols-4", className)} aria-busy aria-label="Loading">
      {Array.from({ length: count }, (_, i) => (
        <Skeleton key={i} className="h-28 rounded-xl" />
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="space-y-2" aria-busy aria-label="Loading">
      <Skeleton className="h-9 w-full" />
      {Array.from({ length: rows }, (_, i) => (
        <Skeleton key={i} className="h-11 w-full" />
      ))}
    </div>
  );
}

export function FullPageLoader({ label = "Loading SeatWise" }: { label?: string }) {
  return (
    <div className="flex min-h-dvh items-center justify-center" aria-busy aria-label={label}>
      <div className="grid grid-cols-3 gap-1.5">
        {Array.from({ length: 9 }, (_, i) => (
          <span
            key={i}
            className="size-3 animate-pulse rounded-[3px] bg-primary"
            style={{ animationDelay: `${(i % 3) * 120 + Math.floor(i / 3) * 120}ms`, opacity: i % 2 ? 0.45 : 1 }}
          />
        ))}
      </div>
    </div>
  );
}
