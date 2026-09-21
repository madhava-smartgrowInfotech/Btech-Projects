import { Calculator, CheckCircle2, FileCheck2, ListOrdered, Scale, Wallet } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";

import { CitationSheet, type CitationTarget } from "@/components/chat/CitationSheet";
import { FaithfulnessBadge } from "@/components/chat/FaithfulnessBadge";
import { CheckStatusIcon, verdictMeta } from "@/components/common/Badges";
import { SourceChip } from "@/components/policy/SourceChip";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import { useToggleChecklist } from "@/lib/queries";
import type { ClaimCase, ClauseRef } from "@/lib/types";
import { cn, formatDate, formatINR, formatMs } from "@/lib/utils";

const TAGS = /\s*\[C\d+(?:\s*[,;]\s*C?\d+)*\]/g;

export function ClaimResultView({ claim }: { claim: ClaimCase }) {
  const r = claim.result;
  const meta = verdictMeta[r.verdict];
  const Icon = meta.icon;
  const toggle = useToggleChecklist(claim.id);
  const [target, setTarget] = useState<CitationTarget | null>(null);
  const citations = new Map(r.citations.map((c) => [c.ordinal, c]));
  const done = r.documents.filter((d) => claim.checklist_state[d.id]).length;

  const open = (ref: ClauseRef) => {
    if (!ref.ordinal || !ref.page) return;
    const c = citations.get(ref.ordinal);
    setTarget({
      policyId: claim.policy_id,
      ordinal: ref.ordinal,
      label: c?.label ?? ref.label ?? `Clause C${ref.ordinal}`,
      page: ref.page,
      quote: c?.quote,
      bboxes: c?.bboxes,
    });
  };
  const chips = (refs: ClauseRef[] | undefined) =>
    (refs ?? [])
      .filter((ref) => ref.ordinal && ref.page)
      .map((ref, i) => (
        <SourceChip
          key={`${ref.ordinal}-${i}`}
          label={citations.get(ref.ordinal!)?.label ?? ref.label}
          page={ref.page}
          onOpen={() => open(ref)}
        />
      ));

  return (
    <div className="space-y-5">
      <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.3 }}>
        <Card className="relative gap-3 overflow-hidden">
          <div className={cn("absolute inset-y-0 left-0 w-1.5", meta.bar)} />
          <CardHeader className="pl-7">
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <span>{claim.policy_name}</span>·<span>{formatDate(claim.created_at, true)}</span>
            </div>
            <CardTitle className="flex flex-wrap items-center gap-3 text-2xl">
              <span className={cn("inline-flex items-center gap-2", meta.tone)}>
                <Icon className="size-7" /> {meta.label}
              </span>
              <span className="text-lg font-normal text-muted-foreground">for {claim.treatment}</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 pl-7">
            <p className="leading-relaxed">{r.verdict_summary}</p>
            {r.matched_specific_disease && (
              <Badge variant="outline" className="h-auto max-w-full whitespace-normal text-left">
                Listed under the specific-disease waiting period as “{r.matched_specific_disease}”
              </Badge>
            )}
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <FaithfulnessBadge faithfulness={r.faithfulness} />
              <span>Checked in {formatMs(r.timings.total_ms as number)}</span>
              <span className="hidden sm:inline">· {r.model}</span>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card className="gap-3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Scale className="size-4 text-primary" /> Why
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {r.reasons.map((reason, i) => (
                <li key={i} className="space-y-1.5">
                  <p className="text-sm leading-relaxed">{reason.text.replace(TAGS, "")}</p>
                  <div className="flex flex-wrap gap-1.5">{chips(reason.clauses)}</div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card className="gap-3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <CheckCircle2 className="size-4 text-primary" /> Eligibility pre-checks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="divide-y">
              {r.prechecks.map((c, i) => (
                <li key={i} className="flex gap-3 py-2.5">
                  <span className="mt-0.5">
                    <CheckStatusIcon status={c.status} />
                  </span>
                  <div className="min-w-0 flex-1 space-y-1">
                    <div className="flex flex-wrap items-center gap-2 text-sm font-medium">
                      {c.check}
                      <Badge variant="outline" className="text-[10px] font-normal text-muted-foreground">
                        {c.source === "rule" ? "Calculated" : "From policy text"}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{c.detail.replace(TAGS, "")}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {chips(c.clauses ?? (c.clause_ordinal ? [{ ordinal: c.clause_ordinal, page: c.page ?? null }] : []))}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>

      {(r.estimate || r.cost_notes.length > 0) && (
        <Card className="gap-3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Wallet className="size-4 text-primary" /> Cost picture
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 lg:grid-cols-[1fr_1.2fr]">
            {r.estimate && (
              <div className="space-y-3 rounded-xl bg-muted/40 p-4">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Calculator className="size-4" /> Estimate for {formatINR(r.estimate.estimated_cost)}
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-lg bg-card p-3">
                    <div className="text-xs text-muted-foreground">Insurer may pay</div>
                    <div className="text-xl font-bold text-success">{formatINR(r.estimate.insurer_pays)}</div>
                  </div>
                  <div className="rounded-lg bg-card p-3">
                    <div className="text-xs text-muted-foreground">You may pay</div>
                    <div className="text-xl font-bold">{formatINR(r.estimate.you_pay)}</div>
                  </div>
                </div>
                <dl className="space-y-1 text-xs text-muted-foreground">
                  {r.estimate.deductible > 0 && (
                    <div className="flex justify-between">
                      <dt>Deductible</dt>
                      <dd>{formatINR(r.estimate.deductible)}</dd>
                    </div>
                  )}
                  {r.estimate.co_payment_percent > 0 && (
                    <div className="flex justify-between">
                      <dt>Co-payment ({r.estimate.co_payment_percent}%)</dt>
                      <dd>{formatINR(r.estimate.co_payment_amount)}</dd>
                    </div>
                  )}
                </dl>
                {r.estimate.notes.map((n) => (
                  <p key={n} className="text-[11px] text-muted-foreground">
                    {n}
                  </p>
                ))}
              </div>
            )}
            <ul className="list-disc space-y-1.5 pl-5 text-sm text-muted-foreground">
              {r.cost_notes.map((n) => (
                <li key={n}>{n.replace(TAGS, "")}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-5 lg:grid-cols-2">
        <Card className="gap-3">
          <CardHeader>
            <CardTitle className="flex items-center justify-between gap-2 text-base">
              <span className="flex items-center gap-2">
                <FileCheck2 className="size-4 text-primary" /> Document checklist
              </span>
              <span className="text-xs font-normal text-muted-foreground">
                {done}/{r.documents.length} ready
              </span>
            </CardTitle>
            <Progress value={r.documents.length ? (done / r.documents.length) * 100 : 0} aria-label="Documents ready" />
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {r.documents.map((d) => {
                const checked = Boolean(claim.checklist_state[d.id]);
                return (
                  <li key={d.id} className={cn("flex gap-3 rounded-lg border p-3 transition-colors", checked && "bg-success/5")}>
                    <Checkbox
                      id={`doc-${d.id}`}
                      checked={checked}
                      onCheckedChange={(v) => toggle.mutate({ itemId: d.id, done: v === true })}
                      className="mt-0.5"
                    />
                    <label htmlFor={`doc-${d.id}`} className="min-w-0 flex-1 cursor-pointer space-y-1">
                      <span className={cn("block text-sm font-medium", checked && "text-muted-foreground line-through")}>{d.item}</span>
                      <span className="block text-xs text-muted-foreground">{d.why.replace(TAGS, "")}</span>
                      <span className="flex flex-wrap gap-1.5">{chips(d.clauses)}</span>
                    </label>
                  </li>
                );
              })}
            </ul>
          </CardContent>
        </Card>

        <Card className="gap-3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <ListOrdered className="size-4 text-primary" /> Claim steps
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="relative space-y-5 border-l pl-6">
              {r.steps.map((s, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.05 }}
                  className="relative"
                >
                  <span className="absolute -left-[37px] grid size-6 place-items-center rounded-full border-2 border-background bg-primary text-xs font-semibold text-primary-foreground">
                    {i + 1}
                  </span>
                  <div className="flex flex-wrap items-center gap-2">
                    <h4 className="font-semibold">{s.title}</h4>
                    {s.timeline && (
                      <Badge variant="secondary" className="text-[11px]">
                        {s.timeline}
                      </Badge>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">{s.detail.replace(TAGS, "")}</p>
                  <div className="mt-1.5 flex flex-wrap gap-1.5">{chips(s.clauses)}</div>
                </motion.li>
              ))}
            </ol>
          </CardContent>
        </Card>
      </div>

      <p className="text-xs text-muted-foreground">
        This guidance is generated from your policy wording and the details you entered. The insurer makes the final claim decision.
      </p>
      <CitationSheet target={target} onClose={() => setTarget(null)} />
    </div>
  );
}
