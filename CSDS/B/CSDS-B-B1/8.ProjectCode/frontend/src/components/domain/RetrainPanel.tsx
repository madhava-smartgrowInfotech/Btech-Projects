import { useMutation, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage } from "@/lib/api";
import { pct } from "@/lib/format";
import { keys, useModelInfo } from "@/lib/queries";
import type { RetrainResult } from "@/lib/types";

/** Officer decisions become labels; one click refits the models and shows held-out before / after metrics. */
export function RetrainPanel({ highlight, className }: { highlight?: boolean; className?: string }) {
  const qc = useQueryClient();
  const info = useModelInfo();
  const [result, setResult] = useState<RetrainResult | null>(null);
  const [error, setError] = useState("");

  const retrain = useMutation({
    mutationFn: async () => (await api.post<RetrainResult>("/model/retrain")).data,
    onMutate: () => setError(""),
    onSuccess: (data) => {
      setResult(data);
      qc.invalidateQueries({ queryKey: keys.model });
      qc.invalidateQueries({ queryKey: ["analytics"] });
      toast.success(`Model retrained: v${data.before?.version ?? "?"} → v${data.after.version}`);
    },
    onError: (err) => {
      setError(errorMessage(err));
      toast.error("Retraining failed", { description: errorMessage(err) });
    },
  });

  const rows =
    result &&
    ([
      ["Category accuracy", result.before?.category.test.accuracy, result.after.category.test.accuracy],
      ["Department accuracy", result.before?.department.test.accuracy, result.after.department.test.accuracy],
      ["Priority accuracy", result.before?.priority.test.accuracy, result.after.priority.test.accuracy],
      ["Agrees with officers (department)", result.after.feedback.officer_agreement_before?.department, result.after.feedback.officer_agreement_after?.department],
      ["Agrees with officers (category)", result.after.feedback.officer_agreement_before?.category, result.after.feedback.officer_agreement_after?.category],
    ] as [string, number | undefined, number | undefined][]);

  return (
    <Card className={className}>
      <CardHeader title="Learn from officer decisions" description="Overrides become training labels." icon={<RefreshCw />} />
      <CardBody className="space-y-3">
        {info.isPending ? (
          <Skeleton className="h-4 w-3/4" />
        ) : info.isError ? (
          <ErrorState error={info.error} title="Couldn't read the model status" onRetry={() => info.refetch()} className="py-6" />
        ) : (
          <p className="text-sm text-muted-foreground">
            Model v{info.data.model_version} · <b className="text-foreground">{info.data.total_officer_labels}</b> officer-reviewed complaints ·{" "}
            <b className="text-foreground">{info.data.new_labels_since_last_run}</b> new overrides since the last run
          </p>
        )}
        {highlight && !result && (
          <p className="rounded-xl border border-warning/30 bg-warning/10 px-3 py-2 text-xs text-warning">
            Your override was saved as a training label. Retrain to teach the model.
          </p>
        )}
        <Button className="w-full" onClick={() => retrain.mutate()} loading={retrain.isPending}>
          {!retrain.isPending && <RefreshCw />} {retrain.isPending ? "Retraining (about a minute)…" : "Retrain model now"}
        </Button>
        {error && (
          <p role="alert" className="text-sm text-danger">
            {error}
          </p>
        )}
        {rows && result && (
          <div className="space-y-2">
            <div className="text-xs font-semibold">
              v{result.before?.version ?? "?"} → v{result.after.version} · {result.after.feedback.labels_used} officer labels · {result.after.train_seconds}s
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[300px] text-xs">
                <caption className="sr-only">Held-out metrics before and after retraining</caption>
                <thead>
                  <tr className="text-left text-muted-foreground">
                    <th scope="col" className="py-1 font-medium">Held-out metric</th>
                    <th scope="col" className="py-1 text-right font-medium">Before</th>
                    <th scope="col" className="py-1 text-right font-medium">After</th>
                  </tr>
                </thead>
                <tbody className="tabular-nums">
                  {rows.map(([k, a, b]) => (
                    <tr key={k} className="border-t border-[var(--glass-border)]">
                      <td className="py-1.5">{k}</td>
                      <td className="py-1.5 text-right text-muted-foreground">{pct(a)}</td>
                      <td className="py-1.5 text-right font-semibold">{pct(b)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {!result && info.data?.runs?.[0] && (
          <p className="text-xs text-muted-foreground">
            Last run: v{info.data.runs[0].version} with {info.data.runs[0].labels_used} labels.
          </p>
        )}
      </CardBody>
    </Card>
  );
}
