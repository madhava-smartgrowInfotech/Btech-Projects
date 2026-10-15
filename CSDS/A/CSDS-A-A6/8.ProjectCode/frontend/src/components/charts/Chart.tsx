import { BarChart3, Table2 } from "lucide-react";
import { useState, type ReactNode } from "react";

import { IconButton } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

/** Series colors for Aurora Glass charts - violet, cyan, magenta first; always drawn as gradients. */
export const SERIES = ["#7C5CFF", "#22D3EE", "#F472B6", "#A3E635", "#FBBF24"] as const;
export const STATUS = {
  good: "#34D399",
  warning: "#FBBF24",
  serious: "#FB923C",
  critical: "#FB7185",
  neutral: "#94A3B8",
} as const;

export interface TableSpec {
  columns: string[];
  rows: (string | number | null)[][];
}

/** A chart in a glass card with a legend and a table view (so no reading depends on color alone). */
export function ChartCard({
  title,
  description,
  legend,
  table,
  empty,
  children,
  className,
  icon,
}: {
  title: string;
  description?: string;
  legend?: { label: string; color: string }[];
  table?: TableSpec;
  empty?: ReactNode;
  children: ReactNode;
  className?: string;
  icon?: ReactNode;
}) {
  const [asTable, setAsTable] = useState(false);
  return (
    <Card className={cn("flex flex-col", className)}>
      <CardHeader
        title={title}
        description={description}
        icon={icon}
        action={
          table && !empty ? (
            <IconButton label={asTable ? "Show chart" : "Show as table"} size="icon-sm" onClick={() => setAsTable((v) => !v)}>
              {asTable ? <BarChart3 /> : <Table2 />}
            </IconButton>
          ) : undefined
        }
      />
      <div className="flex-1 space-y-3 p-5 pt-4">
        {empty ? (
          <div className="grid h-48 place-items-center rounded-xl border border-dashed border-[var(--glass-border)] px-4 text-center text-sm text-muted-foreground">
            {empty}
          </div>
        ) : asTable && table ? (
          <div className="scrollbar-thin max-h-64 overflow-auto rounded-xl border border-[var(--glass-border)]">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-popover text-left text-xs text-muted-foreground">
                <tr>
                  {table.columns.map((c) => (
                    <th key={c} scope="col" className="px-3 py-2 font-medium">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.rows.map((row, i) => (
                  <tr key={i} className="border-t border-[var(--glass-border)]">
                    {row.map((cell, j) => (
                      <td key={j} className={cn("px-3 py-1.5", j > 0 && "tabular-nums")}>
                        {cell ?? "-"}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <>
            {legend && legend.length > 1 && (
              <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground" aria-label="Legend">
                {legend.map((l) => (
                  <li key={l.label} className="flex items-center gap-1.5">
                    <span className="size-2.5 rounded-full" style={{ background: l.color, boxShadow: `0 0 8px ${l.color}` }} />
                    {l.label}
                  </li>
                ))}
              </ul>
            )}
            {children}
          </>
        )}
      </div>
    </Card>
  );
}

interface TooltipPayloadItem {
  name?: string | number;
  value?: number | string;
  color?: string;
  stroke?: string;
  fill?: string;
  dataKey?: string | number;
  payload?: Record<string, unknown>;
}

/** Recharts tooltip in glass. */
export function ChartTooltip({
  active,
  payload,
  label,
  formatter,
  labelFormatter,
}: {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string | number;
  formatter?: (value: number | string, name: string) => string;
  labelFormatter?: (label: string | number) => string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-strong min-w-[150px] rounded-xl bg-popover px-3 py-2 text-xs">
      {label !== undefined && <div className="mb-1 font-medium text-popover-foreground">{labelFormatter ? labelFormatter(label) : label}</div>}
      <ul className="space-y-0.5">
        {payload.map((item) => {
          const color = item.stroke && !item.stroke.startsWith("url") ? item.stroke : item.color && !item.color.startsWith("url") ? item.color : "#7C5CFF";
          return (
            <li key={String(item.dataKey ?? item.name)} className="flex items-center justify-between gap-3">
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <span className="size-2 rounded-full" style={{ background: color }} />
                {item.name}
              </span>
              <span className="font-medium tabular-nums text-popover-foreground">
                {formatter ? formatter(item.value ?? "", String(item.name)) : item.value}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export const axisProps = {
  stroke: "var(--chart-axis)",
  fontSize: 11,
  tickLine: false,
  axisLine: false,
} as const;

export const gridProps = {
  stroke: "var(--chart-grid)",
  strokeDasharray: "3 6",
  vertical: false,
} as const;

/**
 * <defs> with vertical (area) and horizontal (bar) gradients for each series color.
 * Use fill="url(#area-0)" / fill="url(#bar-1)" etc. Put inside any Recharts chart.
 */
export function ChartGradients({ id = "" }: { id?: string }) {
  return (
    <defs>
      {SERIES.map((c, i) => (
        <linearGradient key={`a${i}`} id={`area${id}-${i}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={c} stopOpacity={0.45} />
          <stop offset="100%" stopColor={c} stopOpacity={0} />
        </linearGradient>
      ))}
      {SERIES.map((c, i) => (
        <linearGradient key={`b${i}`} id={`bar${id}-${i}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={c} stopOpacity={1} />
          <stop offset="100%" stopColor={SERIES[(i + 1) % 3]} stopOpacity={0.75} />
        </linearGradient>
      ))}
      {Object.entries(STATUS).map(([k, c]) => (
        <linearGradient key={k} id={`status${id}-${k}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={c} stopOpacity={1} />
          <stop offset="100%" stopColor={c} stopOpacity={0.55} />
        </linearGradient>
      ))}
      <filter id={`glow${id}`} x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="3" result="b" />
        <feMerge>
          <feMergeNode in="b" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>
  );
}

/** Active point with a soft glow - pass as `activeDot={GlowDot("#7C5CFF")}`. */
export function GlowDot(color: string) {
  return function Dot(props: { cx?: number; cy?: number }) {
    const { cx, cy } = props;
    if (cx === undefined || cy === undefined) return <g />;
    return (
      <g>
        <circle cx={cx} cy={cy} r={12} fill={color} opacity={0.18} />
        <circle cx={cx} cy={cy} r={7} fill={color} opacity={0.3} />
        <circle cx={cx} cy={cy} r={4} fill="#fff" stroke={color} strokeWidth={2.5} />
      </g>
    );
  };
}
