import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, ExternalLink, Loader2, Minus, Plus } from "lucide-react";
import { motion } from "motion/react";
import { useEffect, useMemo, useRef, useState, type MouseEvent } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { errorMessage, fetchBlobUrl } from "@/lib/api";
import { useClauses, usePages } from "@/lib/queries";
import type { Clause } from "@/lib/types";
import { cn } from "@/lib/utils";

function usePageImage(policyId: number, page: number) {
  return useQuery({
    queryKey: ["page-image", policyId, page],
    queryFn: () => fetchBlobUrl(`/policies/${policyId}/pages/${page}?scale=1.5`),
    staleTime: Infinity,
    gcTime: 10 * 60_000,
    enabled: page > 0,
  });
}

export async function openOriginalPdf(policyId: number) {
  const win = window.open("", "_blank");
  try {
    const url = await fetchBlobUrl(`/policies/${policyId}/file`);
    if (win) win.location.href = url;
    else window.location.href = url;
  } catch (err) {
    win?.close();
    toast.error(errorMessage(err, "Couldn't open the PDF."));
  }
}

export function PdfPageViewer({
  policyId,
  page,
  onPageChange,
  selectedOrdinal,
  onSelectClause,
}: {
  policyId: number;
  page: number;
  onPageChange: (page: number) => void;
  selectedOrdinal: number | null;
  onSelectClause: (clause: Clause | null) => void;
}) {
  const pages = usePages(policyId);
  const clauses = useClauses(policyId);
  const image = usePageImage(policyId, page);
  usePageImage(policyId, Math.min(page + 1, pages.data?.length ?? page)); // prefetch next page
  const [zoom, setZoom] = useState(1);
  const [hovered, setHovered] = useState<number | null>(null);
  const [pageInput, setPageInput] = useState(String(page));
  const frameRef = useRef<HTMLDivElement>(null);

  useEffect(() => setPageInput(String(page)), [page]);

  const info = pages.data?.[page - 1];
  const total = pages.data?.length ?? 0;
  const onPage = useMemo(
    () => (clauses.data ?? []).filter((c) => c.page_start <= page && c.page_end >= page),
    [clauses.data, page],
  );
  const selected = (clauses.data ?? []).find((c) => c.ordinal === selectedOrdinal) ?? null;
  const boxesFor = (ordinal: number | null) =>
    ordinal === null ? [] : ((clauses.data ?? []).find((c) => c.ordinal === ordinal)?.bboxes ?? []).filter((b) => b.page === page);

  useEffect(() => {
    // Bring the highlighted clause into view once the page image and clause boxes are both on screen.
    const timer = window.setTimeout(() => {
      const frame = frameRef.current;
      const el = frame?.querySelector<HTMLElement>("[data-highlight='selected']");
      if (!frame || !el) return;
      const top = el.getBoundingClientRect().top - frame.getBoundingClientRect().top + frame.scrollTop;
      frame.scrollTo({ top: Math.max(0, top - frame.clientHeight / 3), behavior: "smooth" });
    }, 120);
    return () => window.clearTimeout(timer);
  }, [selectedOrdinal, page, image.data, clauses.data]);

  function onImageClick(e: MouseEvent<HTMLDivElement>) {
    if (!info) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * info.width;
    const y = ((e.clientY - rect.top) / rect.height) * info.height;
    const hit = onPage.find((c) => c.bboxes.some((b) => b.page === page && x >= b.x0 - 2 && x <= b.x1 + 2 && y >= b.y0 - 2 && y <= b.y1 + 2));
    onSelectClause(hit ?? null);
  }

  function go(n: number) {
    if (total && n >= 1 && n <= total) onPageChange(n);
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
      <div className="min-w-0 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="icon-sm" onClick={() => go(page - 1)} disabled={page <= 1} aria-label="Previous page">
            <ChevronLeft />
          </Button>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              go(Number(pageInput));
            }}
            className="flex items-center gap-1.5 text-sm"
          >
            <Input
              value={pageInput}
              onChange={(e) => setPageInput(e.target.value.replace(/\D/g, ""))}
              className="h-8 w-14 text-center"
              aria-label="Page number"
            />
            <span className="text-muted-foreground">of {total || "…"}</span>
          </form>
          <Button variant="outline" size="icon-sm" onClick={() => go(page + 1)} disabled={!total || page >= total} aria-label="Next page">
            <ChevronRight />
          </Button>
          <div className="ml-auto flex items-center gap-1">
            <Button variant="ghost" size="icon-sm" onClick={() => setZoom((z) => Math.max(0.6, +(z - 0.2).toFixed(1)))} aria-label="Zoom out">
              <Minus />
            </Button>
            <span className="w-12 text-center text-xs tabular-nums text-muted-foreground">{Math.round(zoom * 100)}%</span>
            <Button variant="ghost" size="icon-sm" onClick={() => setZoom((z) => Math.min(2, +(z + 0.2).toFixed(1)))} aria-label="Zoom in">
              <Plus />
            </Button>
            <Button variant="outline" size="sm" onClick={() => openOriginalPdf(policyId)}>
              <ExternalLink /> Original PDF
            </Button>
          </div>
        </div>

        <div ref={frameRef} className="max-h-[78vh] overflow-auto rounded-xl border bg-muted/40 p-2 sm:p-4">
          <div className="mx-auto" style={{ maxWidth: `${Math.round(760 * zoom)}px` }}>
            {info && image.data ? (
              <div
                className="relative cursor-crosshair overflow-hidden rounded-md bg-white shadow-sm"
                style={{ aspectRatio: `${info.width} / ${info.height}` }}
                onClick={onImageClick}
              >
                <img src={image.data} alt={`Page ${page} of the policy`} className="absolute inset-0 size-full" draggable={false} />
                {[...boxesFor(hovered !== selectedOrdinal ? hovered : null).map((b) => ({ b, kind: "hover" as const })),
                  ...boxesFor(selectedOrdinal).map((b) => ({ b, kind: "selected" as const }))].map(({ b, kind }, i) => (
                  <motion.div
                    key={`${kind}-${i}-${b.x0}-${b.y0}`}
                    data-highlight={kind}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className={cn(
                      "pointer-events-none absolute rounded-sm",
                      kind === "selected"
                        ? "bg-amber-300/35 ring-2 ring-amber-500/80 mix-blend-multiply"
                        : "bg-teal-400/15 ring-1 ring-teal-600/50",
                    )}
                    style={{
                      left: `${((b.x0 - 3) / info.width) * 100}%`,
                      top: `${((b.y0 - 2) / info.height) * 100}%`,
                      width: `${((b.x1 - b.x0 + 6) / info.width) * 100}%`,
                      height: `${((b.y1 - b.y0 + 4) / info.height) * 100}%`,
                    }}
                  />
                ))}
              </div>
            ) : image.isError ? (
              <div className="grid aspect-[3/4] place-items-center text-sm text-destructive">{errorMessage(image.error)}</div>
            ) : (
              <div className="relative">
                <Skeleton className="aspect-[3/4] w-full rounded-md" />
                <Loader2 className="absolute inset-0 m-auto size-6 animate-spin text-muted-foreground" />
              </div>
            )}
          </div>
        </div>
        <p className="text-xs text-muted-foreground">Tip: click any paragraph on the page to see which clause it belongs to.</p>
      </div>

      <aside className="space-y-3">
        <div className="rounded-xl border bg-card p-4">
          <div className="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">Selected clause</div>
          {selected ? (
            <div className="space-y-2">
              <div className="font-semibold leading-snug">{selected.label}</div>
              {selected.section_path && <div className="text-xs text-muted-foreground">{selected.section_path}</div>}
              <div className="text-xs text-muted-foreground">
                Page {selected.page_start}
                {selected.page_end !== selected.page_start && `-${selected.page_end}`}
              </div>
              <ScrollArea className="h-48 pr-3">
                <p className="whitespace-pre-line text-sm leading-relaxed">{selected.text}</p>
              </ScrollArea>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Click a citation, a Policy Card source or a paragraph on the page.</p>
          )}
        </div>
        <div className="rounded-xl border bg-card p-4">
          <div className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Clauses on this page</div>
          {clauses.isLoading ? (
            <Skeleton className="h-24" />
          ) : onPage.length === 0 ? (
            <p className="text-sm text-muted-foreground">No text clauses on this page.</p>
          ) : (
            <ul className="max-h-72 space-y-1 overflow-auto pr-1">
              {onPage.map((c) => (
                <li key={c.ordinal}>
                  <button
                    type="button"
                    onMouseEnter={() => setHovered(c.ordinal)}
                    onMouseLeave={() => setHovered(null)}
                    onFocus={() => setHovered(c.ordinal)}
                    onBlur={() => setHovered(null)}
                    onClick={() => onSelectClause(c)}
                    className={cn(
                      "w-full rounded-md px-2 py-1.5 text-left text-xs transition-colors hover:bg-accent",
                      c.ordinal === selectedOrdinal && "bg-accent font-medium text-accent-foreground",
                    )}
                  >
                    <span className="line-clamp-2">{c.label}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>
    </div>
  );
}
