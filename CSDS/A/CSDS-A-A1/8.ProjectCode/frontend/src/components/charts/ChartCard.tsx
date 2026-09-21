import { BarChart3, Table2 } from "lucide-react";
import { useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface TableSpec {
  columns: string[];
  rows: (string | number | null)[][];
}

/** A chart with a title, an optional legend and a table view (so no reading depends on color alone). */
export function ChartCard({
  title,
  description,
  legend,
  table,
  empty,
  children,
  className,
}: {
  title: string;
  description?: string;
  legend?: { label: string; color: string }[];
  table?: TableSpec;
  empty?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  const [asTable, setAsTable] = useState(false);
  return (
    <Card className={cn("gap-3", className)}>
      <CardHeader className="flex flex-row items-start justify-between gap-2 space-y-0">
        <div className="min-w-0 space-y-1">
          <CardTitle className="text-base">{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </div>
        {table && !empty && (
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setAsTable((v) => !v)}
            aria-label={asTable ? "Show chart" : "Show as table"}
            title={asTable ? "Show chart" : "Show as table"}
          >
            {asTable ? <BarChart3 /> : <Table2 />}
          </Button>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {empty ? (
          <div className="grid h-48 place-items-center rounded-lg bg-muted/40 px-4 text-center text-sm text-muted-foreground">
            {empty}
          </div>
        ) : asTable && table ? (
          <div className="max-h-64 overflow-auto rounded-lg border">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-xs text-muted-foreground">
                <tr>
                  {table.columns.map((c) => (
                    <th key={c} className="px-3 py-2 font-medium">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.rows.map((row, i) => (
                  <tr key={i} className="border-t">
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
                    <span className="size-2.5 rounded-sm" style={{ background: l.color }} />
                    {l.label}
                  </li>
                ))}
              </ul>
            )}
            {children}
          </>
        )}
      </CardContent>
    </Card>
  );
}

interface TooltipPayloadItem {
  name?: string | number;
  value?: number | string;
  color?: string;
  dataKey?: string | number;
  payload?: Record<string, unknown>;
}

/** Recharts tooltip content in the app's popover style; values in text colors, swatch carries identity. */
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
    <div className="min-w-[140px] rounded-lg border bg-popover px-3 py-2 text-xs shadow-md">
      {label !== undefined && (
        <div className="mb-1 font-medium text-popover-foreground">{labelFormatter ? labelFormatter(label) : label}</div>
      )}
      <ul className="space-y-0.5">
        {payload.map((item) => (
          <li key={String(item.dataKey ?? item.name)} className="flex items-center justify-between gap-3">
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <span className="size-2 rounded-sm" style={{ background: item.color }} />
              {item.name}
            </span>
            <span className="font-medium tabular-nums text-popover-foreground">
              {formatter ? formatter(item.value ?? "", String(item.name)) : item.value}
            </span>
          </li>
        ))}
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
