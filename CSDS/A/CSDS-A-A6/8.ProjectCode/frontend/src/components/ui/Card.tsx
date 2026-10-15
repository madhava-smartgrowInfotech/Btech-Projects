import { forwardRef, type HTMLAttributes, type ReactNode } from "react";

import { cn } from "@/lib/utils";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Light sweep on hover (default on). */
  sweep?: boolean;
  /** Lift slightly on hover - for clickable cards. */
  interactive?: boolean;
  strong?: boolean;
}

/** Glass card: translucent fill, blur, 1px border, layered shadow and a bright top-edge highlight. */
export const Card = forwardRef<HTMLDivElement, CardProps>(function Card(
  { className, sweep = true, interactive, strong, ...props },
  ref,
) {
  return (
    <div
      ref={ref}
      className={cn(
        strong ? "glass-strong" : "glass",
        "rounded-2xl text-card-foreground",
        sweep && "sweep",
        interactive &&
          "transition-[transform,box-shadow,border-color] duration-300 hover:-translate-y-0.5 hover:border-[color-mix(in_srgb,var(--violet)_40%,var(--glass-border))]",
        className,
      )}
      {...props}
    />
  );
});

export function CardHeader({
  title,
  description,
  action,
  icon,
  className,
}: {
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  icon?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex items-start justify-between gap-3 px-5 pt-5", className)}>
      <div className="flex min-w-0 items-start gap-3">
        {icon && (
          <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-grad-soft text-violet-ink ring-1 ring-[var(--glass-border)] [&_svg]:size-[18px]">
            {icon}
          </span>
        )}
        <div className="min-w-0 space-y-0.5">
          <h3 className="font-display text-base font-semibold leading-tight">{title}</h3>
          {description && <p className="text-sm text-muted-foreground">{description}</p>}
        </div>
      </div>
      {action && <div className="flex shrink-0 items-center gap-1">{action}</div>}
    </div>
  );
}

export function CardBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-5", className)} {...props} />;
}
