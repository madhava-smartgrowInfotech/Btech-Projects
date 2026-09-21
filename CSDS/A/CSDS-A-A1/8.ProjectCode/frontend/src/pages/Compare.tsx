import { ArrowLeftRight, BadgeCheck, Columns2, Crown, Lightbulb, Loader2, Minus, Trash2 } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { toast } from "sonner";

import { CitationSheet, type CitationTarget } from "@/components/chat/CitationSheet";
import { SeverityBadge } from "@/components/common/Badges";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { LanguageSelect } from "@/components/common/LanguageSelect";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState } from "@/components/common/States";
import { SourceChip } from "@/components/policy/SourceChip";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useComparison, useComparisons, useCreateComparison, useDeleteComparison, usePolicies } from "@/lib/queries";
import type { Comparison, Language, Severity } from "@/lib/types";
import { cn, timeAgo } from "@/lib/utils";

function Picker() {
  const { user } = useAuth();
  const policies = usePolicies();
  const create = useCreateComparison();
  const navigate = useNavigate();
  const withCards = policies.data?.filter((p) => p.document.status === "ready" && p.has_card) ?? [];
  const [a, setA] = useState<string>("");
  const [b, setB] = useState<string>("");
  const [language, setLanguage] = useState<Language>(user?.language ?? "en");

  if (policies.isLoading) return <Skeleton className="h-48" />;
  if (withCards.length < 2) {
    return (
      <EmptyState
        icon={<Columns2 />}
        title="You need two policies to compare"
        description="Upload a second policy wording (or add the sample policies). Each needs its Policy Card before it can be compared."
        action={
          <Button asChild>
            <Link to="/app/policies">Go to My policies</Link>
          </Button>
        }
      />
    );
  }

  const run = () =>
    create.mutate(
      { policy_a_id: Number(a), policy_b_id: Number(b), language },
      { onSuccess: (c) => navigate(`/app/compare/${c.id}`), onError: (e) => toast.error(errorMessage(e)) },
    );

  return (
    <Card className="gap-4">
      <CardHeader>
        <CardTitle className="text-base">Choose two policies</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid items-end gap-3 md:grid-cols-[1fr_auto_1fr]">
          {[
            ["Policy A", a, setA, b],
            ["Policy B", b, setB, a],
          ].map(([label, value, setter, other], i) => (
            <div key={String(label)} className={cn("space-y-1.5", i === 1 && "md:order-3")}>
              <Label>{String(label)}</Label>
              <Select value={String(value)} onValueChange={setter as (v: string) => void}>
                <SelectTrigger className="w-full" aria-label={String(label)}>
                  <SelectValue placeholder="Select a policy" />
                </SelectTrigger>
                <SelectContent>
                  {withCards.map((p) => (
                    <SelectItem key={p.id} value={String(p.id)} disabled={String(p.id) === other}>
                      {p.display_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ))}
          <Button
            variant="ghost"
            size="icon"
            className="mx-auto md:order-2"
            onClick={() => {
              setA(b);
              setB(a);
            }}
            aria-label="Swap policies"
          >
            <ArrowLeftRight />
          </Button>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <LanguageSelect value={language} onChange={setLanguage} />
          <Button onClick={run} disabled={!a || !b || a === b || create.isPending}>
            {create.isPending ? <Loader2 className="animate-spin" /> : <Columns2 />}
            {create.isPending ? "Comparing…" : "Compare"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function Result({ comparison }: { comparison: Comparison }) {
  const r = comparison.result;
  const [target, setTarget] = useState<CitationTarget | null>(null);
  const names = { a: comparison.policy_a_name, b: comparison.policy_b_name };
  const policyIds = { a: comparison.policy_a_id, b: comparison.policy_b_id };
  const severities: Severity[] = ["high", "medium", "low"];
  const wins = { a: r.rows.filter((x) => x.better === "a").length, b: r.rows.filter((x) => x.better === "b").length };

  return (
    <div className="space-y-5">
      <Card className="gap-3 border-primary/20 bg-gradient-to-br from-accent/50 to-card">
        <CardContent className="space-y-4 pt-6">
          <p className="leading-relaxed">{r.overall}</p>
          <div className="grid gap-3 sm:grid-cols-2">
            {(["a", "b"] as const).map((side) => (
              <div key={side} className="rounded-xl border bg-card p-4">
                <div className="mb-1 flex items-center gap-2">
                  <Badge className="size-6 justify-center rounded-full p-0">{side.toUpperCase()}</Badge>
                  <span className="truncate font-semibold">{names[side]}</span>
                </div>
                <div className="mb-2 flex flex-wrap gap-1.5 text-xs text-muted-foreground">
                  {severities.map((s) =>
                    r.risk_counts[side][s] ? (
                      <span key={s} className="inline-flex items-center gap-1">
                        <SeverityBadge severity={s} /> {r.risk_counts[side][s]}
                      </span>
                    ) : null,
                  )}
                  <span className="inline-flex items-center gap-1">
                    <Crown className="size-3.5 text-primary" /> Better on {wins[side]} measurable items
                  </span>
                </div>
                <div className="text-xs font-medium text-muted-foreground">Choose {side.toUpperCase()} if…</div>
                <ul className="mt-1 list-disc space-y-0.5 pl-5 text-sm">
                  {(side === "a" ? r.choose_a_if : r.choose_b_if).map((x) => (
                    <li key={x}>{x}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="gap-3">
        <CardHeader>
          <CardTitle className="text-base">Side by side</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b text-left text-xs text-muted-foreground">
                <th className="w-1/4 py-2 pr-3 font-medium">Item</th>
                <th className="py-2 pr-3 font-medium">A · {names.a}</th>
                <th className="py-2 font-medium">B · {names.b}</th>
              </tr>
            </thead>
            <tbody>
              {r.rows.map((row) => (
                <tr key={row.key} className="border-b align-top last:border-0">
                  <td className="py-2.5 pr-3 font-medium">{row.label}</td>
                  {(["a", "b"] as const).map((side) => {
                    const cell = row[side];
                    const better = row.better === side;
                    return (
                      <td key={side} className={cn("py-2.5 pr-3", better && "bg-success/5")}>
                        <div className="flex items-start gap-1.5">
                          {better && <BadgeCheck className="mt-0.5 size-4 shrink-0 text-success" aria-label="Better" />}
                          {row.better === "equal" && <Minus className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-label="Same" />}
                          <span className={cn(!cell.found && "italic text-muted-foreground")}>{cell.value ?? "-"}</span>
                        </div>
                        {cell.found && cell.page && (
                          <SourceChip
                            label={cell.clause_ordinal ? `C${cell.clause_ordinal}` : "Source"}
                            page={cell.page}
                            verified={cell.verified ?? undefined}
                            onOpen={() =>
                              setTarget({ policyId: policyIds[side], ordinal: cell.clause_ordinal, label: `${names[side]} - ${row.label}`, page: cell.page! })
                            }
                            className="mt-1"
                          />
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-xs text-muted-foreground">A tick marks the better value where the direction is clear (for example a shorter waiting period).</p>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {r.trade_offs.map((t, i) => (
          <motion.div key={t.topic} initial={{ opacity: 0, y: 8 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.04 }}>
            <Card className="h-full gap-2">
              <CardHeader>
                <CardTitle className="flex items-center justify-between gap-2 text-base">
                  {t.topic}
                  <Badge variant={t.better === "A" || t.better === "B" ? "default" : "secondary"}>
                    {t.better === "A" || t.better === "B" ? `${t.better} is better` : "Depends"}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>
                  <span className="font-medium">A:</span> {t.policy_a}
                </p>
                <p>
                  <span className="font-medium">B:</span> {t.policy_b}
                </p>
                <p className="text-muted-foreground">{t.why}</p>
                <div className="flex flex-wrap gap-1.5">
                  {t.tags.map((tag, j) => (
                    <Badge key={j} variant="outline" className="font-mono text-[10px]">
                      {tag.policy.toUpperCase()}:C{tag.ordinal}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {r.next_actions.length > 0 && (
        <Card className="gap-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Lightbulb className="size-4 text-primary" /> Recommended next steps
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc space-y-1 pl-5 text-sm">
              {r.next_actions.map((x) => (
                <li key={x}>{x}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
      <p className="text-xs text-muted-foreground">
        Compared from both Policy Cards by {r.model}. Premiums are not part of the policy wording and are not compared.
      </p>
      <CitationSheet target={target} onClose={() => setTarget(null)} />
    </div>
  );
}

export default function Compare() {
  const { comparisonId } = useParams();
  const id = comparisonId ? Number(comparisonId) : null;
  const comparison = useComparison(id);
  const history = useComparisons();
  const del = useDeleteComparison();
  const navigate = useNavigate();

  return (
    <div>
      <PageHeader
        title="Compare plans"
        description="Put two policies side by side: cover, limits, waiting periods, exclusions and the trade-offs between them."
        actions={
          id && (
            <Button asChild variant="outline">
              <Link to="/app/compare">
                <Columns2 /> New comparison
              </Link>
            </Button>
          )
        }
      />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
        <div className="min-w-0">
          {!id ? (
            <Picker />
          ) : comparison.isError ? (
            <ErrorState error={comparison.error} onRetry={() => comparison.refetch()} />
          ) : comparison.isLoading || !comparison.data ? (
            <Skeleton className="h-96" />
          ) : (
            <Result comparison={comparison.data} />
          )}
        </div>
        <aside className="lg:sticky lg:top-20 lg:self-start">
          <Card className="gap-3">
            <CardHeader>
              <CardTitle className="text-base">Saved comparisons</CardTitle>
            </CardHeader>
            <CardContent>
              {history.isLoading ? (
                <Skeleton className="h-20" />
              ) : !history.data?.length ? (
                <p className="text-sm text-muted-foreground">Your comparisons will appear here.</p>
              ) : (
                <ul className="space-y-1">
                  {history.data.map((c) => (
                    <li key={c.id} className="group relative">
                      <Link to={`/app/compare/${c.id}`} className={cn("block rounded-lg px-3 py-2 pr-9 text-sm hover:bg-accent", c.id === id && "bg-accent")}>
                        <div className="truncate font-medium">{c.policy_a_name}</div>
                        <div className="truncate text-muted-foreground">vs {c.policy_b_name}</div>
                        <div className="text-xs text-muted-foreground">{timeAgo(c.created_at)}</div>
                      </Link>
                      <ConfirmDialog
                        trigger={
                          <Button variant="ghost" size="icon-xs" className="absolute right-1.5 top-2.5 opacity-0 group-hover:opacity-100 focus-visible:opacity-100" aria-label="Delete comparison">
                            <Trash2 />
                          </Button>
                        }
                        title="Delete this comparison?"
                        description="You can run it again at any time."
                        confirmLabel="Delete"
                        destructive
                        onConfirm={() =>
                          del.mutate(c.id, {
                            onSuccess: () => c.id === id && navigate("/app/compare"),
                            onError: (e) => toast.error(errorMessage(e)),
                          })
                        }
                      />
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}
