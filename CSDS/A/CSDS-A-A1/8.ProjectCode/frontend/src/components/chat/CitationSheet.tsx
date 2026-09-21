import { useQuery } from "@tanstack/react-query";
import { ExternalLink, Loader2 } from "lucide-react";
import { Link } from "react-router";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { fetchBlobUrl } from "@/lib/api";
import { usePages } from "@/lib/queries";
import type { BBox } from "@/lib/types";

export interface CitationTarget {
  policyId: number;
  ordinal: number | null;
  label: string;
  page: number;
  quote?: string | null;
  bboxes?: BBox[];
}

/** Side sheet showing the cited clause on its PDF page, highlighted. */
export function CitationSheet({ target, onClose }: { target: CitationTarget | null; onClose: () => void }) {
  const pages = usePages(target?.policyId ?? NaN, Boolean(target));
  const image = useQuery({
    queryKey: ["page-image", target?.policyId, target?.page],
    queryFn: () => fetchBlobUrl(`/policies/${target!.policyId}/pages/${target!.page}?scale=1.5`),
    enabled: Boolean(target),
    staleTime: Infinity,
  });
  const info = target ? pages.data?.[target.page - 1] : undefined;
  const boxes = (target?.bboxes ?? []).filter((b) => b.page === target?.page);

  return (
    <Sheet open={Boolean(target)} onOpenChange={(o) => !o && onClose()}>
      <SheetContent side="right" className="w-full gap-0 p-0 sm:max-w-xl">
        {target && (
          <>
            <SheetHeader className="border-b p-4">
              <SheetTitle className="pr-6 leading-snug">{target.label}</SheetTitle>
              <SheetDescription>Page {target.page} of the policy wording</SheetDescription>
            </SheetHeader>
            <ScrollArea className="h-[calc(100dvh-8.5rem)]">
              <div className="space-y-4 p-4">
                {target.quote && (
                  <blockquote className="rounded-lg border-l-4 border-amber-500 bg-amber-50 p-3 text-sm italic dark:bg-amber-400/10">
                    “{target.quote}”
                  </blockquote>
                )}
                <div className="rounded-lg border bg-muted/40 p-2">
                  {info && image.data ? (
                    <div className="relative overflow-hidden rounded bg-white" style={{ aspectRatio: `${info.width} / ${info.height}` }}>
                      <img src={image.data} alt={`Page ${target.page}`} className="absolute inset-0 size-full" />
                      {boxes.map((b, i) => (
                        <div
                          key={i}
                          className="absolute rounded-sm bg-amber-300/35 ring-2 ring-amber-500/80 mix-blend-multiply"
                          style={{
                            left: `${((b.x0 - 3) / info.width) * 100}%`,
                            top: `${((b.y0 - 2) / info.height) * 100}%`,
                            width: `${((b.x1 - b.x0 + 6) / info.width) * 100}%`,
                            height: `${((b.y1 - b.y0 + 4) / info.height) * 100}%`,
                          }}
                        />
                      ))}
                    </div>
                  ) : (
                    <div className="grid aspect-[3/4] place-items-center">
                      <Loader2 className="size-6 animate-spin text-muted-foreground" />
                    </div>
                  )}
                </div>
              </div>
            </ScrollArea>
            <div className="border-t p-3">
              <Button asChild variant="outline" className="w-full">
                <Link
                  to={`/app/policies/${target.policyId}?tab=document&page=${target.page}${target.ordinal ? `&clause=${target.ordinal}` : ""}`}
                  onClick={onClose}
                >
                  <ExternalLink /> Open in document viewer
                </Link>
              </Button>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
