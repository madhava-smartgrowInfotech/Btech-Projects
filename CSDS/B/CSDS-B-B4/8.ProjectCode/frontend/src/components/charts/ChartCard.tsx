import { useState, type ReactNode } from "react";
import { BarChart3, Table2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export interface TableView {
  columns: string[];
  rows: (string | number)[][];
}

/** Card wrapper for every chart: title, optional legend, and a table view (the chart's accessible twin). */
export function ChartCard({
  title,
  subtitle,
  legend,
  table,
  children,
  className,
  actions,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  legend?: { label: string; color: string }[];
  table?: TableView;
  children: ReactNode;
  className?: string;
  actions?: ReactNode;
}) {
  const { t } = useI18n();
  const [asTable, setAsTable] = useState(false);
  return (
    <section className={cn("surface flex flex-col p-4 sm:p-5", className)}>
      <header className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="font-display text-base font-semibold">{title}</h2>
          {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
        </div>
        <div className="flex shrink-0 items-center gap-1">
          {actions}
          {table && (
            <Button variant="ghost" size="sm" onClick={() => setAsTable((v) => !v)} aria-pressed={asTable} className="h-8 px-2 text-xs">
              {asTable ? <BarChart3 className="mr-1 h-3.5 w-3.5" /> : <Table2 className="mr-1 h-3.5 w-3.5" />}
              {asTable ? t("chart.chart") : t("chart.table")}
            </Button>
          )}
        </div>
      </header>
      {legend && legend.length > 1 && !asTable && (
        <ul className="mb-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
          {legend.map((l) => (
            <li key={l.label} className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ background: l.color }} />
              {l.label}
            </li>
          ))}
        </ul>
      )}
      {asTable && table ? (
        <div className="max-h-72 overflow-auto rounded-lg border">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-muted text-left text-xs text-muted-foreground">
              <tr>
                {table.columns.map((c) => (
                  <th key={c} className="px-3 py-2 font-medium">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((r, i) => (
                <tr key={i} className="border-t">
                  {r.map((v, j) => (
                    <td key={j} className={cn("px-3 py-1.5", typeof v === "number" && "text-right tabular")}>
                      {v}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="min-h-0 flex-1">{children}</div>
      )}
    </section>
  );
}

/** Tooltip body shared by all Recharts charts (text uses ink tokens, the swatch carries identity). */
export function ChartTooltip({ active, payload, label, format }: { active?: boolean; payload?: { name?: string; value?: number; color?: string; dataKey?: string }[]; label?: string; format?: (v: number) => string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-lift">
      {label && <p className="mb-1 font-medium text-foreground">{label}</p>}
      {payload.map((p) => (
        <p key={String(p.dataKey)} className="flex items-center gap-2 text-muted-foreground">
          <span className="h-2 w-2 rounded-full" style={{ background: p.color }} />
          <span>{p.name}</span>
          <span className="ml-auto pl-3 font-medium tabular text-foreground">{format ? format(Number(p.value)) : p.value}</span>
        </p>
      ))}
    </div>
  );
}

export const axisProps = {
  stroke: "var(--chart-axis)",
  tick: { fill: "var(--chart-muted)", fontSize: 11 },
  tickLine: false,
  axisLine: { stroke: "var(--chart-axis)" },
} as const;
