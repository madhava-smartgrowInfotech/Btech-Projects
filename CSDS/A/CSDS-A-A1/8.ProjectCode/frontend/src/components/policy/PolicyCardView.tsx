import { BadgeCheck, CalendarClock, CircleSlash, Info, Lightbulb, ListChecks, ShieldAlert, Target } from "lucide-react";
import { motion } from "motion/react";
import type { ReactNode } from "react";

import { SourceChip } from "@/components/policy/SourceChip";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { PolicyCardResponse, Sourced } from "@/lib/types";
import { formatDate } from "@/lib/utils";

type OpenSource = (page: number, ordinal: number | null) => void;

function Fact({ label, item, onOpen }: { label: string; item?: Sourced; onOpen: OpenSource }) {
  if (!item) return null;
  return (
    <div className="flex min-w-0 flex-col gap-1.5 rounded-lg border bg-card p-3">
      <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className={item.found ? "text-sm font-medium leading-snug" : "text-sm italic text-muted-foreground"}>{item.value}</div>
      {item.found && item.page && (
        <SourceChip
          label={item.clause_label}
          page={item.page}
          verified={item.verified}
          quote={item.quote}
          onOpen={() => onOpen(item.page!, item.clause_ordinal)}
          className="self-start"
        />
      )}
    </div>
  );
}

function ListBlock({ title, icon, items, onOpen }: { title: string; icon: ReactNode; items: Sourced[]; onOpen: OpenSource }) {
  if (!items?.length) return null;
  return (
    <Card className="gap-3">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base [&_svg]:size-4 [&_svg]:text-primary">
          {icon} {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="divide-y">
          {items.map((item, i) => (
            <li key={i} className="flex flex-col gap-1 py-2.5 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
              <div className="min-w-0">
                <div className="text-sm font-medium">{item.name}</div>
                <div className="text-sm text-muted-foreground">{item.value}</div>
              </div>
              {item.page && (
                <SourceChip
                  label={item.clause_label}
                  page={item.page}
                  verified={item.verified}
                  quote={item.quote}
                  onOpen={() => onOpen(item.page!, item.clause_ordinal)}
                  className="shrink-0 self-start"
                />
              )}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

export function PolicyCardView({ card, onOpenSource }: { card: PolicyCardResponse; onOpenSource: OpenSource }) {
  const d = card.data;
  const fields = card.labels.fields;
  const summary = card.summary;
  const facts = Object.entries(fields);
  const container = { hidden: {}, show: { transition: { staggerChildren: 0.03 } } };
  const itemAnim = { hidden: { opacity: 0, y: 6 }, show: { opacity: 1, y: 0 } };

  return (
    <div className="space-y-6">
      <Card className="gap-4 border-primary/20 bg-gradient-to-br from-accent/50 via-card to-card">
        <CardHeader>
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <Badge variant="secondary">{d.policy_type}</Badge>
            {d.uin && <Badge variant="outline" className="font-mono">UIN {d.uin}</Badge>}
            <span className="inline-flex items-center gap-1">
              <BadgeCheck className="size-3.5 text-success" /> {Math.round(card.verified_ratio * 100)}% of values verified in the text
            </span>
          </div>
          <CardTitle className="text-xl">
            {d.product_name} <span className="font-normal text-muted-foreground">by {d.insurer}</span>
          </CardTitle>
        </CardHeader>
        {summary && (
          <CardContent className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
            <div className="space-y-3">
              <p className="leading-relaxed">{summary.overview}</p>
              {summary.best_for?.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5">
                  <Target className="size-4 text-primary" />
                  <span className="text-xs font-medium text-muted-foreground">Suits:</span>
                  {summary.best_for.map((b) => (
                    <Badge key={b} variant="outline" className="h-auto max-w-full shrink whitespace-normal bg-background text-left">
                      {b}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
            <div className="space-y-3">
              {summary.watch_outs?.length > 0 && (
                <div>
                  <div className="mb-1 flex items-center gap-1.5 text-sm font-semibold">
                    <ShieldAlert className="size-4 text-warning" /> Watch out for
                  </div>
                  <ul className="list-disc space-y-0.5 pl-5 text-sm text-muted-foreground">
                    {summary.watch_outs.map((w) => (
                      <li key={w}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}
              {summary.next_actions?.length > 0 && (
                <div>
                  <div className="mb-1 flex items-center gap-1.5 text-sm font-semibold">
                    <Lightbulb className="size-4 text-primary" /> Recommended next steps
                  </div>
                  <ul className="list-disc space-y-0.5 pl-5 text-sm text-muted-foreground">
                    {summary.next_actions.map((w) => (
                      <li key={w}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        )}
      </Card>

      <section>
        <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
          <CalendarClock className="size-5 text-primary" /> Waiting periods
        </h2>
        <motion.div variants={container} initial="hidden" animate="show" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {Object.entries(card.labels.waiting_periods).map(([key, label]) => (
            <motion.div key={key} variants={itemAnim}>
              <Fact label={label} item={d.waiting_periods?.[key]} onOpen={onOpenSource} />
            </motion.div>
          ))}
        </motion.div>
        {d.specific_disease_examples?.length > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-1.5 text-sm">
            <span className="text-xs font-medium text-muted-foreground">Listed for the specific-disease wait:</span>
            {d.specific_disease_examples.map((x) => (
              <Badge key={x} variant="secondary" className="font-normal">
                {x}
              </Badge>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
          <Info className="size-5 text-primary" /> Cover and limits
        </h2>
        <motion.div variants={container} initial="hidden" animate="show" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {facts.map(([key, label]) => (
            <motion.div key={key} variants={itemAnim}>
              <Fact label={label} item={d[key] as Sourced | undefined} onOpen={onOpenSource} />
            </motion.div>
          ))}
        </motion.div>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <ListBlock title="Conditional co-payments" icon={<Info />} items={d.co_payment_conditions} onOpen={onOpenSource} />
        <ListBlock title="Sub-limits" icon={<ListChecks />} items={d.sub_limits} onOpen={onOpenSource} />
        <ListBlock title="Key exclusions" icon={<CircleSlash />} items={d.key_exclusions} onOpen={onOpenSource} />
        <ListBlock
          title="Claim deadlines"
          icon={<CalendarClock />}
          items={Object.entries(card.labels.claim_timelines)
            .map(([k, label]) => ({ ...(d.claim_timelines?.[k] as Sourced), name: label }))
            .filter((x) => x.value)}
          onOpen={onOpenSource}
        />
      </div>

      <p className="text-xs text-muted-foreground">
        Extracted from the policy wording by {card.model} on {formatDate(card.created_at)}
        {card.translated && " · translated for display; quotes stay in the original English"}. Values with a warning icon could not be matched
        word-for-word in the text.
      </p>
    </div>
  );
}
