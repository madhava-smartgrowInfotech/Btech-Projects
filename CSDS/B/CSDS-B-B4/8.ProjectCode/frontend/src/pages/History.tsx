import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useInfiniteQuery } from "@tanstack/react-query";
import { History as HistoryIcon, Loader2, QrCode, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, ListSkeleton, PageHeader } from "@/components/common/States";
import { LevelBadge, PartyRow, StatusBadge } from "@/components/risk/RiskBits";
import { GuideButton } from "@/components/voice/SpeakButton";
import { api } from "@/lib/api";
import { formatDate, formatINR, formatTime } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import type { Payment } from "@/lib/types";
import { cn } from "@/lib/utils";

const PAGE = 25;

export default function History() {
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const [direction, setDirection] = useState<"all" | "sent" | "received">("all");
  const [level, setLevel] = useState<"all" | "low" | "medium" | "high">("all");
  const [q, setQ] = useState("");

  const query = useInfiniteQuery({
    queryKey: ["payments", "history", direction, level, q],
    queryFn: async ({ pageParam }) => (await api.get<{ items: Payment[]; has_more: boolean; offset: number }>("/payments", { params: { direction, level, q: q || undefined, limit: PAGE, offset: pageParam } })).data,
    initialPageParam: 0,
    getNextPageParam: (last) => (last.has_more ? last.offset + PAGE : undefined),
  });

  const groups = useMemo(() => {
    const items = query.data?.pages.flatMap((p) => p.items) ?? [];
    const map = new Map<string, Payment[]>();
    for (const p of items) {
      const key = formatDate(p.created_at, lang);
      map.set(key, [...(map.get(key) ?? []), p]);
    }
    return [...map.entries()];
  }, [query.data, lang]);

  const chip = (active: boolean) => cn("rounded-full border px-3 py-1.5 text-sm transition", active ? "border-primary bg-primary text-primary-foreground" : "hover:border-primary/40");

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title={t("nav.history")} subtitle={t("history.subtitle")} actions={<GuideButton screen="history" />} />
      <div className="mb-4 space-y-3">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("history.search")} className="pl-9" />
        </div>
        <div className="flex flex-wrap gap-2" role="group" aria-label={t("history.direction")}>
          {(["all", "sent", "received"] as const).map((d) => (
            <button key={d} className={chip(direction === d)} onClick={() => setDirection(d)} aria-pressed={direction === d}>
              {t(`history.dir.${d}`)}
            </button>
          ))}
          <span className="mx-1 w-px bg-border" />
          {(["all", "low", "medium", "high"] as const).map((l) => (
            <button key={l} className={chip(level === l)} onClick={() => setLevel(l)} aria-pressed={level === l}>
              {l === "all" ? t("history.all_levels") : t(`risk.level.${l}`)}
            </button>
          ))}
        </div>
      </div>

      {query.isLoading ? (
        <ListSkeleton rows={6} />
      ) : query.isError ? (
        <ErrorState error={query.error} onRetry={() => query.refetch()} />
      ) : groups.length === 0 ? (
        <EmptyState icon={HistoryIcon} title={t("history.empty")} description={t("history.empty_hint")} />
      ) : (
        <div className="space-y-5">
          {groups.map(([day, items]) => (
            <section key={day}>
              <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{day}</h2>
              <ul className="surface divide-y">
                {items.map((p) => (
                  <li key={p.id}>
                    <button className="flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-muted/40" onClick={() => navigate(`/app/history/${p.id}`)}>
                      <PartyRow
                        className="flex-1"
                        party={p.counterparty}
                        sub={
                          <span className="flex flex-wrap items-center gap-x-2">
                            {formatTime(p.created_at, lang)}
                            {p.channel === "qr" && <QrCode className="h-3 w-3" />}
                            {p.channel === "collect" && <span>{t("history.via_request")}</span>}
                            <StatusBadge status={p.status} />
                          </span>
                        }
                        right={
                          <div className="flex flex-col items-end gap-1">
                            <span className={cn("font-semibold tabular", p.direction === "received" && "text-safe", ["cancelled", "blocked", "rejected"].includes(p.status) && "text-muted-foreground line-through")}>
                              {p.direction === "received" ? "+" : "−"}
                              {formatINR(p.amount)}
                            </span>
                            {p.direction === "sent" && <LevelBadge level={p.level} blocked={p.status === "blocked"} />}
                          </div>
                        }
                      />
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ))}
          {query.hasNextPage && (
            <div className="flex justify-center">
              <Button variant="outline" onClick={() => query.fetchNextPage()} disabled={query.isFetchingNextPage}>
                {query.isFetchingNextPage && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {t("history.more")}
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
