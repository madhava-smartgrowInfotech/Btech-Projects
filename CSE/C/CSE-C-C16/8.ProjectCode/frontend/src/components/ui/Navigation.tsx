import { motion } from "framer-motion";
import { Check, ChevronRight } from "lucide-react";
import { Tabs as TabsPrimitive } from "radix-ui";
import { Fragment, useId, type ReactNode } from "react";
import { Link } from "react-router";

import { cn } from "@/lib/utils";

/** Tabs with a sliding gradient indicator. Content is rendered by the caller via <TabPanel>. */
export function Tabs({
  value,
  onValueChange,
  tabs,
  children,
  className,
  listClassName,
}: {
  value: string;
  onValueChange: (value: string) => void;
  tabs: { value: string; label: ReactNode; icon?: ReactNode; count?: number }[];
  children: ReactNode;
  className?: string;
  listClassName?: string;
}) {
  const id = useId();
  return (
    <TabsPrimitive.Root value={value} onValueChange={onValueChange} className={className}>
      <TabsPrimitive.List
        className={cn(
          "glass-flat no-scrollbar relative flex w-full gap-1 overflow-x-auto rounded-2xl p-1 sm:inline-flex sm:w-auto",
          listClassName,
        )}
      >
        {tabs.map((t) => (
          <TabsPrimitive.Trigger
            key={t.value}
            value={t.value}
            className="relative inline-flex h-9 shrink-0 items-center gap-2 rounded-xl px-3.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground data-[state=active]:text-foreground [&_svg]:size-4"
          >
            {value === t.value && (
              <motion.span
                layoutId={`tab-${id}`}
                className="glass-strong absolute inset-0 rounded-xl"
                transition={{ type: "spring", stiffness: 480, damping: 38 }}
              />
            )}
            <span className="relative inline-flex items-center gap-2">
              {t.icon}
              {t.label}
              {t.count !== undefined && (
                <span className="rounded-full bg-grad-primary px-1.5 text-[10px] font-semibold leading-4 text-white">{t.count}</span>
              )}
            </span>
          </TabsPrimitive.Trigger>
        ))}
      </TabsPrimitive.List>
      {children}
    </TabsPrimitive.Root>
  );
}

export function TabPanel({ value, children, className }: { value: string; children: ReactNode; className?: string }) {
  return (
    <TabsPrimitive.Content value={value} className={cn("mt-5 outline-none", className)}>
      {children}
    </TabsPrimitive.Content>
  );
}

export function Breadcrumbs({ items, className }: { items: { label: ReactNode; to?: string }[]; className?: string }) {
  return (
    <nav aria-label="Breadcrumb" className={cn("min-w-0", className)}>
      <ol className="flex min-w-0 items-center gap-1 text-sm text-muted-foreground">
        {items.map((item, i) => {
          const last = i === items.length - 1;
          return (
            <Fragment key={i}>
              <li className={cn("min-w-0", last ? "truncate font-medium text-foreground" : "shrink-0")}>
                {item.to && !last ? (
                  <Link to={item.to} className="rounded transition-colors hover:text-foreground">
                    {item.label}
                  </Link>
                ) : (
                  <span aria-current={last ? "page" : undefined}>{item.label}</span>
                )}
              </li>
              {!last && (
                <li aria-hidden className="shrink-0">
                  <ChevronRight className="size-3.5 opacity-60" />
                </li>
              )}
            </Fragment>
          );
        })}
      </ol>
    </nav>
  );
}

export type StepState = "done" | "current" | "upcoming" | "error";

/** Horizontal (default) or vertical stepper. Steps can be clickable when `onStepClick` is given. */
export function Stepper({
  steps,
  current,
  onStepClick,
  orientation = "horizontal",
  className,
  states,
}: {
  steps: { label: ReactNode; description?: ReactNode }[];
  current: number;
  onStepClick?: (index: number) => void;
  orientation?: "horizontal" | "vertical";
  className?: string;
  /** Override the state of individual steps (e.g. an error step). */
  states?: StepState[];
}) {
  const vertical = orientation === "vertical";
  return (
    <ol className={cn(vertical ? "space-y-0" : "flex items-start gap-2", className)}>
      {steps.map((step, i) => {
        const state: StepState = states?.[i] ?? (i < current ? "done" : i === current ? "current" : "upcoming");
        const clickable = onStepClick && (state === "done" || state === "current");
        const dot = (
          <span
            className={cn(
              "relative grid size-8 shrink-0 place-items-center rounded-full text-xs font-semibold transition-all",
              state === "done" && "bg-grad-primary text-white shadow-[0_0_14px_-2px_rgba(34,160,107,0.7)]",
              state === "current" && "bg-[var(--glass-strong)] text-violet-ink ring-2 ring-[var(--violet)]",
              state === "upcoming" && "bg-muted text-muted-foreground ring-1 ring-[var(--glass-border)]",
              state === "error" && "bg-danger/15 text-danger ring-2 ring-danger/60",
            )}
          >
            {state === "current" && <span className="absolute inset-0 animate-ping rounded-full bg-violet/25 [animation-duration:2s]" />}
            {state === "done" ? <Check className="size-4" strokeWidth={3} /> : i + 1}
          </span>
        );
        const text = (
          <span className="min-w-0">
            <span
              className={cn(
                "block text-sm font-medium",
                state === "upcoming" ? "text-muted-foreground" : "text-foreground",
                state === "error" && "text-danger",
              )}
            >
              {step.label}
            </span>
            {step.description && <span className="block text-xs text-muted-foreground">{step.description}</span>}
          </span>
        );
        const Inner = clickable ? "button" : "div";
        return (
          <li
            key={i}
            className={cn(vertical ? "relative flex gap-3 pb-5 last:pb-0" : "relative flex min-w-0 flex-1 flex-col items-center gap-2 text-center")}
            aria-current={state === "current" ? "step" : undefined}
          >
            {vertical && i < steps.length - 1 && (
              <span
                aria-hidden
                className={cn("absolute left-4 top-9 h-[calc(100%-2.5rem)] w-px -translate-x-1/2", i < current ? "bg-grad-primary" : "bg-[var(--glass-border)]")}
              />
            )}
            <Inner
              {...(clickable ? { type: "button" as const, onClick: () => onStepClick?.(i) } : {})}
              className={cn(
                vertical ? "flex items-start gap-3 text-left" : "flex flex-col items-center gap-2",
                clickable && "rounded-lg",
              )}
            >
              {dot}
              <span className={cn(!vertical && "hidden sm:block")}>{text}</span>
            </Inner>
            {!vertical && i < steps.length - 1 && (
              <span
                aria-hidden
                className={cn(
                  "absolute left-[calc(50%+1.25rem)] right-[calc(-50%+1.25rem)] top-4 h-px",
                  i < current ? "bg-grad-primary" : "bg-[var(--glass-border)]",
                )}
              />
            )}
          </li>
        );
      })}
    </ol>
  );
}
