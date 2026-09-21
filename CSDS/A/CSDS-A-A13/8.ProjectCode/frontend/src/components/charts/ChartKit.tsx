import { useState, type ReactNode } from "react";
import { BarChart3, Table2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

/** Series colours in the fixed categorical order (never cycled). */
export const SERIES = ["var(--paper-1)", "var(--paper-2)", "var(--paper-3)", "var(--paper-4)", "var(--paper-5)", "var(--paper-6)", "var(--paper-7)", "var(--paper-8)"];
export const STATUS = { good: "hsl(var(--success))", bad: "hsl(var(--destructive))", neutral: "hsl(var(--muted-foreground) / 0.35)" };

export const axisProps = {
  tick: { fill: "hsl(var(--muted-foreground))", fontSize: 11 },
  tickLine: false,
  axisLine: { stroke: "hsl(var(--border))" },
} as const;
export const gridProps = { stroke: "hsl(var(--border))", strokeDasharray: "", vertical: false } as const;
export const barProps = { maxBarSize: 24, radius: [4, 4, 0, 0] as [number, number, number, number], stroke: "hsl(var(--card))", strokeWidth: 2 };

interface TooltipEntry {
  name?: string | number;
  value?: number | string;
  color?: string;
  dataKey?: string | number;
  payload?: Record<string, unknown>;
}

/** Tooltip in the product's own surface and text tokens (text never takes the series colour). */
export function ChartTooltip({
  active, payload, label, format = (v) => String(v), labelFormat,
}: {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string | number;
  format?: (value: number | string, name?: string) => string;
  labelFormat?: (label: string | number | undefined, payload?: TooltipEntry[]) => ReactNode;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="min-w-40 rounded-lg border bg-popover px-3 py-2 text-xs shadow-lift">
      <div className="mb-1.5 font-medium text-foreground">{labelFormat ? labelFormat(label, payload) : label}</div>
      <div className="space-y-1">
        {payload.map((p) => (
          <div key={String(p.dataKey ?? p.name)} className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <span className="size-2 rounded-sm" style={{ background: p.color }} />
              {p.name}
            </span>
            <span className="font-medium tabular text-foreground">{format(p.value ?? 0, String(p.name))}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function Legend({ items }: { items: { label: string; color: string }[] }) {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1.5" aria-hidden>
      {items.map((i) => (
        <span key={i.label} className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
          <span className="size-2.5 rounded-sm" style={{ background: i.color }} />
          {i.label}
        </span>
      ))}
    </div>
  );
}

/** A chart with a title, optional legend, and a table view of the same numbers. */
export function ChartCard({
  title, description, legend, table, children, className, height = 260,
}: {
  title: string;
  description?: string;
  legend?: { label: string; color: string }[];
  table?: { columns: string[]; rows: (string | number)[][] };
  children: ReactNode;
  className?: string;
  height?: number;
}) {
  const [asTable, setAsTable] = useState(false);
  return (
    <Card className={cn("min-w-0", className)}>
      <CardHeader className="flex-row items-start justify-between gap-3 space-y-0">
        <div className="min-w-0">
          <CardTitle className="text-base">{title}</CardTitle>
          {description && <CardDescription className="mt-1">{description}</CardDescription>}
        </div>
        {table && (
          <Button variant="ghost" size="icon-sm" onClick={() => setAsTable((v) => !v)} aria-label={asTable ? "Show chart" : "Show as table"} title={asTable ? "Show chart" : "Show as table"}>
            {asTable ? <BarChart3 /> : <Table2 />}
          </Button>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {legend && legend.length > 1 && !asTable && <Legend items={legend} />}
        {asTable && table ? (
          <div className="max-h-[320px] overflow-auto scrollbar-thin">
            <Table>
              <TableHeader>
                <TableRow>
                  {table.columns.map((c) => (
                    <TableHead key={c} className="normal-case">{c}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {table.rows.map((r, i) => (
                  <TableRow key={i}>
                    {r.map((v, j) => (
                      <TableCell key={j} className={cn("text-xs", j > 0 && "tabular")}>{v}</TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          <div style={{ height }} className="w-full">{children}</div>
        )}
      </CardContent>
    </Card>
  );
}

/** A labelled number tile. `hero` is used for the single most important figure of a view. */
export function StatTile({
  label, value, hint, icon: Icon, hero = false, tone,
}: {
  label: string;
  value: string;
  hint?: string;
  icon?: React.ComponentType<{ className?: string }>;
  hero?: boolean;
  tone?: "good" | "bad";
}) {
  return (
    <Card className={cn(hero && "bg-primary text-primary-foreground")}>
      <CardContent className="p-5">
        <div className={cn("flex items-center justify-between text-xs", hero ? "text-primary-foreground/80" : "text-muted-foreground")}>
          {label}
          {Icon && <Icon className={cn("size-4", tone === "good" && !hero && "text-success", tone === "bad" && !hero && "text-destructive")} />}
        </div>
        <div className={cn("mt-2 font-display font-semibold", hero ? "text-5xl" : "text-3xl")}>{value}</div>
        {hint && <div className={cn("mt-1 text-xs", hero ? "text-primary-foreground/80" : "text-muted-foreground")}>{hint}</div>}
      </CardContent>
    </Card>
  );
}
