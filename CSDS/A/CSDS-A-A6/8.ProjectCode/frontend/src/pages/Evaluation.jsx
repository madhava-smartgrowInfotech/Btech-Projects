import { useQuery } from "@tanstack/react-query";
import { FlaskConical, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ErrorState, EmptyState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { StatCard } from "@/components/ui/Display";
import { Table } from "@/components/ui/Table";
import { evalApi } from "@/lib/api.js";
import { humanize, pct } from "@/lib/format.js";
import { keys } from "@/lib/queries.js";

export default function Evaluation() {
  const query = useQuery({
    queryKey: keys.evaluation,
    queryFn: async () => (await evalApi.getMetrics()).data,
  });

  const data = query.data;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Evaluation"
        title="How well ClauseGuard performs"
        description="Scores are measured on a held-out set. Nothing here is hand-picked or estimated."
        actions={data?.generated_at ? <Badge tone="neutral">Run {data.generated_at.slice(0, 10)}</Badge> : null}
      />

      {query.isPending && (
        <div className="grid gap-4 sm:grid-cols-3" role="status" aria-label="Loading evaluation results">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-32 rounded-2xl" />
          ))}
        </div>
      )}

      {query.isError && (
        <ErrorState
          error={query.error}
          title="Couldn't load the evaluation results"
          hint="Make sure the backend is running on port 8106, then try again."
          onRetry={() => query.refetch()}
        />
      )}

      {data && !data.available && (
        <EmptyState
          icon={<FlaskConical />}
          title="No evaluation results yet"
          description={data.message || "Run the evaluation script to generate results."}
        />
      )}

      {data?.available && data.predatory_detection && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard
              label="Precision"
              value={data.predatory_detection.precision}
              format={pct}
              hint="Share of flagged clauses that were truly predatory"
              icon={<ShieldCheck />}
            />
            <StatCard
              label="Recall"
              value={data.predatory_detection.recall}
              format={pct}
              hint="Share of predatory clauses that were flagged"
              accent="cyan"
            />
            <StatCard
              label="F1 score"
              value={data.predatory_detection.f1}
              format={pct}
              hint={`Across ${data.predatory_detection.num_examples} curated examples`}
              accent="magenta"
            />
          </div>

          <Card>
            <CardHeader title="Predatory-clause detection, per rule" description="Counts from the held-out set. TP = caught, FN = missed, FP = false alarm." />
            <CardBody>
              <Table
                caption="Per-rule detection results"
                rowKey={(r) => r.key}
                rows={Object.entries(data.predatory_detection.per_rule ?? {}).map(([key, v]) => ({ key, ...v }))}
                columns={[
                  { key: "rule", header: "Rule", cell: (r) => humanize(r.key), sortValue: (r) => humanize(r.key) },
                  { key: "tp", header: "TP", cell: (r) => r.tp, align: "right", sortValue: (r) => r.tp },
                  { key: "fp", header: "FP", cell: (r) => r.fp, align: "right", sortValue: (r) => r.fp },
                  { key: "fn", header: "FN", cell: (r) => r.fn, align: "right", sortValue: (r) => r.fn },
                  { key: "precision", header: "Precision", cell: (r) => pct(r.precision), align: "right", sortValue: (r) => r.precision },
                  { key: "recall", header: "Recall", cell: (r) => pct(r.recall), align: "right", sortValue: (r) => r.recall },
                ]}
              />
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="CUAD clause classification" description="Which CUAD category each clause is assigned to." />
            <CardBody>
              {data.cuad_classification ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  <StatCard label="Top-1 accuracy" value={data.cuad_classification.top1_accuracy} format={pct} />
                  <StatCard label="Top-3 accuracy" value={data.cuad_classification.top3_accuracy} format={pct} accent="cyan" />
                </div>
              ) : (
                <EmptyState
                  icon={<FlaskConical />}
                  title="Not measured yet"
                  description="This needs a live Gemini key. Add GEMINI_API_KEY to .env, then run python ml/eval.py from the backend venv."
                />
              )}
            </CardBody>
          </Card>
        </>
      )}
    </div>
  );
}
