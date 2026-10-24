import { ArrowRight, BookOpenText, SearchX } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router";

import { SeverityBadge } from "@/components/agri/bits";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { CardsSkeleton, EmptyState, ErrorState } from "@/components/ui/Feedback";
import { SearchField } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { cn } from "@/lib/utils";
import { useLang } from "@/lib/i18n";
import { useDiseases } from "@/lib/queries";

export default function Encyclopedia() {
  const { t } = useLang();
  const q = useDiseases();
  const [search, setSearch] = useState("");
  const [crop, setCrop] = useState("");

  const crops = useMemo(() => [...new Set((q.data ?? []).map((d) => d.crop))].sort(), [q.data]);
  const cards = useMemo(() => {
    const s = search.trim().toLowerCase();
    return (q.data ?? []).filter(
      (d) => (!crop || d.crop === crop) && (!s || (d.name + d.crop + d.symptoms).toLowerCase().includes(s)),
    );
  }, [q.data, search, crop]);

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("guide.title", "Crop disease encyclopedia")}
        description={q.data ? `${q.data.length} entries across ${crops.length} crops: symptoms, treatments and prevention.` : "Symptoms, treatments and prevention."}
      />
      <SearchField value={search} onChange={setSearch} label="Search diseases" placeholder="Search e.g. blight, tomato, mildew…" />

      {crops.length > 0 && (
        <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by crop">
          <button
            type="button"
            aria-pressed={!crop}
            onClick={() => setCrop("")}
            className={cn("rounded-full border px-3 py-1 text-xs font-medium transition-colors", !crop ? "border-transparent bg-grad-primary text-white" : "border-[var(--glass-border)] text-muted-foreground hover:text-foreground")}
          >
            All crops
          </button>
          {crops.map((c) => (
            <button
              key={c}
              type="button"
              aria-pressed={crop === c}
              onClick={() => setCrop(crop === c ? "" : c)}
              className={cn("rounded-full border px-3 py-1 text-xs font-medium transition-colors", crop === c ? "border-transparent bg-grad-primary text-white" : "border-[var(--glass-border)] text-muted-foreground hover:text-foreground")}
            >
              {c}
            </button>
          ))}
        </div>
      )}

      {q.isError ? (
        <ErrorState error={q.error} title="Couldn't load the disease guide" onRetry={() => q.refetch()} />
      ) : q.isPending ? (
        <CardsSkeleton count={6} />
      ) : cards.length === 0 ? (
        <EmptyState
          icon={<SearchX />}
          title="No disease matches"
          description="Try a different word, or clear the crop filter."
          action={
            <Button
              variant="secondary"
              onClick={() => {
                setSearch("");
                setCrop("");
              }}
            >
              Clear search
            </Button>
          }
        />
      ) : (
        <Stagger key={`${search}|${crop}`} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((d) => (
            <StaggerItem key={d.class}>
              <Card interactive className="h-full">
                <Link to={`/disease/${encodeURIComponent(d.class)}`} className="flex h-full flex-col gap-2 p-5" aria-label={`${d.name}: view treatment guide`}>
                  <div className="flex items-center gap-2">
                    <SeverityBadge severity={d.severity} />
                    <span className="ml-auto text-xs text-muted-foreground">{d.crop}</span>
                  </div>
                  <h2 className="font-display font-semibold leading-snug">{d.name}</h2>
                  <p className="line-clamp-2 text-xs text-muted-foreground">{d.symptoms}</p>
                  <span className="mt-auto inline-flex items-center gap-1 pt-2 text-xs font-medium text-violet-ink">
                    View treatment guide <ArrowRight className="size-3.5" aria-hidden />
                  </span>
                </Link>
              </Card>
            </StaggerItem>
          ))}
        </Stagger>
      )}
      {!q.isPending && !q.isError && (
        <p className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <BookOpenText className="size-3.5" aria-hidden /> Showing {cards.length} of {q.data?.length}
        </p>
      )}
    </div>
  );
}
