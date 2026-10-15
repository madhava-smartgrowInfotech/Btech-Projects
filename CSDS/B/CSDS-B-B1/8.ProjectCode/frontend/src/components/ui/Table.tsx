import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";

import { IconButton } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

export interface Column<T> {
  key: string;
  header: ReactNode;
  cell: (row: T) => ReactNode;
  /** Value used for sorting; column is sortable when given. */
  sortValue?: (row: T) => string | number | null;
  align?: "left" | "right" | "center";
  className?: string;
  /** Hide this column in the phone card layout. */
  hideOnCard?: boolean;
}

/**
 * Sortable, paginated glass table. Below `sm` it renders each row as a card so wide tables
 * never overflow a phone screen.
 */
export function Table<T>({
  columns,
  rows,
  rowKey,
  pageSize = 10,
  empty,
  onRowClick,
  initialSort,
  caption,
  className,
}: {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  pageSize?: number;
  empty?: ReactNode;
  onRowClick?: (row: T) => void;
  initialSort?: { key: string; dir: "asc" | "desc" };
  caption?: string;
  className?: string;
}) {
  const [sort, setSort] = useState(initialSort ?? null);
  const [page, setPage] = useState(0);

  const sorted = useMemo(() => {
    if (!sort) return rows;
    const col = columns.find((c) => c.key === sort.key);
    if (!col?.sortValue) return rows;
    const get = col.sortValue;
    return [...rows].sort((a, b) => {
      const va = get(a);
      const vb = get(b);
      if (va === vb) return 0;
      if (va === null) return 1;
      if (vb === null) return -1;
      const cmp = typeof va === "number" && typeof vb === "number" ? va - vb : String(va).localeCompare(String(vb));
      return sort.dir === "asc" ? cmp : -cmp;
    });
  }, [rows, sort, columns]);

  const pages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const safePage = Math.min(page, pages - 1);
  const visible = sorted.slice(safePage * pageSize, safePage * pageSize + pageSize);

  if (rows.length === 0 && empty) return <>{empty}</>;

  function toggle(key: string) {
    setPage(0);
    setSort((s) => (s?.key !== key ? { key, dir: "asc" } : s.dir === "asc" ? { key, dir: "desc" } : null));
  }

  const alignCls = (a?: string) => (a === "right" ? "text-right" : a === "center" ? "text-center" : "text-left");

  return (
    <div className={cn("space-y-3", className)}>
      {/* Desktop / tablet table */}
      <div className="glass hidden overflow-x-auto rounded-2xl sm:block">
        <table className="w-full text-sm">
          {caption && <caption className="sr-only">{caption}</caption>}
          <thead>
            <tr className="border-b border-[var(--glass-border)] text-xs uppercase tracking-wide text-muted-foreground">
              {columns.map((c) => {
                const active = sort?.key === c.key;
                return (
                  <th
                    key={c.key}
                    scope="col"
                    aria-sort={active ? (sort.dir === "asc" ? "ascending" : "descending") : undefined}
                    className={cn("px-4 py-3 font-medium", alignCls(c.align), c.className)}
                  >
                    {c.sortValue ? (
                      <button
                        type="button"
                        onClick={() => toggle(c.key)}
                        className={cn("inline-flex items-center gap-1 rounded transition-colors hover:text-foreground", active && "text-foreground")}
                      >
                        {c.header}
                        {active ? (
                          sort.dir === "asc" ? <ArrowUp className="size-3" /> : <ArrowDown className="size-3" />
                        ) : (
                          <ArrowUpDown className="size-3 opacity-50" />
                        )}
                      </button>
                    ) : (
                      c.header
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {visible.map((row) => (
              <tr
                key={rowKey(row)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={cn(
                  "border-b border-[var(--glass-border)] transition-colors last:border-0",
                  onRowClick && "cursor-pointer hover:bg-[var(--glass-hover)]",
                )}
              >
                {columns.map((c) => (
                  <td key={c.key} className={cn("px-4 py-3 align-middle", alignCls(c.align), c.className)}>
                    {c.cell(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Phone cards */}
      <ul className="space-y-2 sm:hidden">
        {visible.map((row) => (
          <li
            key={rowKey(row)}
            onClick={onRowClick ? () => onRowClick(row) : undefined}
            className={cn("glass space-y-2 rounded-2xl p-4", onRowClick && "cursor-pointer")}
          >
            {columns
              .filter((c) => !c.hideOnCard)
              .map((c, i) => (
                <div key={c.key} className={cn("flex items-start justify-between gap-3 text-sm", i === 0 && "font-medium")}>
                  {i > 0 && <span className="shrink-0 text-xs text-muted-foreground">{c.header}</span>}
                  <span className={cn("min-w-0", i > 0 && "text-right")}>{c.cell(row)}</span>
                </div>
              ))}
          </li>
        ))}
      </ul>

      {pages > 1 && (
        <div className="flex items-center justify-between gap-3 text-xs text-muted-foreground">
          <span className="tabular-nums">
            {safePage * pageSize + 1}-{Math.min(sorted.length, (safePage + 1) * pageSize)} of {sorted.length}
          </span>
          <div className="flex items-center gap-1">
            <IconButton label="Previous page" size="icon-sm" disabled={safePage === 0} onClick={() => setPage(safePage - 1)}>
              <ChevronLeft />
            </IconButton>
            <span className="px-1 tabular-nums">
              {safePage + 1} / {pages}
            </span>
            <IconButton label="Next page" size="icon-sm" disabled={safePage >= pages - 1} onClick={() => setPage(safePage + 1)}>
              <ChevronRight />
            </IconButton>
          </div>
        </div>
      )}
    </div>
  );
}
