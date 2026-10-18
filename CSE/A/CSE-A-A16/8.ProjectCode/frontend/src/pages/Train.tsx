import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Database, Dumbbell, Hand, Play, RefreshCw, SlidersHorizontal, Square, TriangleAlert } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";

import { TrainingCharts } from "@/components/charts/TrainingCharts";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, ProgressBar, Skeleton } from "@/components/ui/Feedback";
import { FormField, Input } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { ConfirmModal } from "@/components/ui/Overlay";
import { toast } from "@/components/ui/Toast";
import { endpoints, errorMessage } from "@/lib/api";
import { classLabel, pct } from "@/lib/format";
import { keys, useConfig, useDataset, useModel, useTrainStatus } from "@/lib/queries";
import { cn } from "@/lib/utils";

function parseIntIn(text: string, min: number, max: number, what: string): [number | null, string | undefined] {
  const n = Number(text);
  if (text.trim() === "" || !Number.isInteger(n)) return [null, `${what} must be a whole number.`];
  if (n < min || n > max) return [null, `${what} must be between ${min} and ${max}.`];
  return [n, undefined];
}

export default function Train() {
  const qc = useQueryClient();
  const config = useConfig();
  const dataset = useDataset();
  const model = useModel();
  const status = useTrainStatus();
  const defaults = config.data?.training_defaults;
  const [epochs, setEpochs] = useState("");
  const [batch, setBatch] = useState("");
  const [lr, setLr] = useState("");
  const [touched, setTouched] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  // fill the form with the desktop defaults once they are known
  useEffect(() => {
    if (defaults && epochs === "" && batch === "" && lr === "") {
      setEpochs(String(defaults.epochs));
      setBatch(String(defaults.batch_size));
      setLr(String(defaults.learning_rate));
    }
  }, [defaults, epochs, batch, lr]);

  const [epochsN, epochsErr] = parseIntIn(epochs, 1, 500, "Epochs");
  const [batchN, batchErr] = parseIntIn(batch, 1, 1024, "Batch size");
  const lrN = Number(lr);
  const lrErr = lr.trim() === "" || !Number.isFinite(lrN) || lrN < 1e-6 || lrN > 1 ? "Learning rate must be a number from 0.000001 to 1." : undefined;
  const formOk = !epochsErr && !batchErr && !lrErr;

  const s = status.data;
  const running = s?.state === "loading" || s?.state === "training";

  // announce finish / failure once
  const prev = useRef<string | undefined>(undefined);
  useEffect(() => {
    if (!s) return;
    if (prev.current && prev.current !== s.state) {
      if (s.state === "done") {
        toast.success("Training finished", { description: s.summary ? `Test accuracy ${pct(s.summary.test_accuracy)}. The model is ready to use.` : undefined });
      } else if (s.state === "error") {
        toast.error("Training failed", { description: s.error ?? undefined });
      }
      if (s.state === "done" || s.state === "error") {
        qc.invalidateQueries({ queryKey: keys.model });
        qc.invalidateQueries({ queryKey: keys.health });
        qc.invalidateQueries({ queryKey: keys.dataset });
      }
    }
    prev.current = s.state;
  }, [s, qc]);

  const start = useMutation({
    mutationFn: () => endpoints.trainStart({ epochs: epochsN!, batch_size: batchN!, learning_rate: lrN }),
    onSuccess: (data) => {
      qc.setQueryData(keys.train, data);
      qc.invalidateQueries({ queryKey: keys.health });
      toast.info("Training started", { description: "Loading and preprocessing the images first." });
    },
    onError: (e) => toast.error("Couldn't start training", { description: errorMessage(e) }),
  });
  const stop = useMutation({
    mutationFn: endpoints.trainStop,
    onSuccess: (data) => {
      qc.setQueryData(keys.train, data);
      toast.info("Stopping after the current epoch…");
    },
    onError: (e) => toast.error("Couldn't stop training", { description: errorMessage(e) }),
  });

  function requestStart() {
    setTouched(true);
    if (!formOk) return;
    if (model.data?.trained) setConfirmOpen(true);
    else start.mutate();
  }

  const withData = dataset.data ? dataset.data.trainable_classes : [];
  const maxCount = Math.max(1, ...Object.values(dataset.data?.counts ?? {}));
  const statusLine = !s
    ? ""
    : s.state === "idle"
      ? "Idle"
      : s.state === "loading"
        ? s.data.total
          ? `Preprocessing images: ${s.data.done}/${s.data.total}`
          : "Loading & preprocessing the dataset…"
        : s.state === "training"
          ? `Epoch ${s.epoch}/${s.epochs}${s.history.accuracy.length ? ` · acc ${pct(s.history.accuracy.at(-1))}` : ""}${s.history.val_accuracy.length ? ` · val_acc ${pct(s.history.val_accuracy.at(-1))}` : ""}`
          : s.state === "done"
            ? `Done. Test accuracy: ${pct(s.summary?.test_accuracy)}`
            : `Error: ${s.error}`;
  const progress = !s ? 0 : s.state === "loading" ? (s.data.total ? (s.data.done / s.data.total) * 100 : 0) : s.state === "done" ? 100 : s.epochs ? (s.epoch / s.epochs) * 100 : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Model"
        title="Train model"
        description="Train the CNN on the images you collected. The best model by validation accuracy is saved and used straight away."
      />

      {(config.isError || dataset.isError) && (
        <ErrorState
          error={config.error ?? dataset.error}
          title="Couldn't reach the SignSpeak server"
          hint="Start it with run.bat, then try again."
          onRetry={() => {
            config.refetch();
            dataset.refetch();
          }}
        />
      )}

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader
              title="Dataset"
              icon={<Database />}
              action={
                <Button size="sm" variant="ghost" onClick={() => dataset.refetch()} loading={dataset.isFetching} aria-label="Refresh counts">
                  <RefreshCw /> Refresh
                </Button>
              }
            />
            <CardBody className="space-y-3">
              {dataset.isPending ? (
                <div className="space-y-2" role="status" aria-label="Loading dataset">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-5 w-full" />
                  ))}
                </div>
              ) : withData.length === 0 ? (
                <EmptyState
                  icon={<Database />}
                  title="No training images yet"
                  description="Collect at least two classes with images, or drop a dataset into data/<class>/."
                  action={
                    <Button asChild>
                      <Link to="/app/collect">Collect data</Link>
                    </Button>
                  }
                />
              ) : (
                <>
                  <p className="text-sm text-muted-foreground">
                    <span className="font-medium text-foreground tabular-nums">{dataset.data!.total.toLocaleString("en-US")}</span> images across{" "}
                    <span className="font-medium text-foreground">{withData.length}</span> classes
                    {!dataset.data!.ready_to_train && " - you need at least 2 classes to train."}
                  </p>
                  <ul className="scrollbar-thin max-h-60 space-y-1.5 overflow-y-auto pr-1" aria-label="Images per class">
                    {withData.map((c) => {
                      const n = dataset.data!.counts[c];
                      return (
                        <li key={c} className="flex items-center gap-2 text-xs">
                          <span className="w-12 shrink-0 font-medium">{classLabel(c)}</span>
                          <span className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                            <span className="block h-full rounded-full bg-grad-primary" style={{ width: `${(n / maxCount) * 100}%` }} />
                          </span>
                          <span className="w-12 shrink-0 text-right tabular-nums text-muted-foreground">{n}</span>
                        </li>
                      );
                    })}
                  </ul>
                </>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Hyperparameters" icon={<SlidersHorizontal />} description="Defaults are the desktop app's." />
            <CardBody className="space-y-4">
              <FormField label="Epochs" error={touched ? epochsErr : undefined} hint="Early stopping may end sooner.">
                {(p) => <Input {...p} inputMode="numeric" value={epochs} onChange={(e) => setEpochs(e.target.value)} disabled={running} />}
              </FormField>
              <FormField label="Batch size" error={touched ? batchErr : undefined}>
                {(p) => <Input {...p} inputMode="numeric" value={batch} onChange={(e) => setBatch(e.target.value)} disabled={running} />}
              </FormField>
              <FormField label="Learning rate" error={touched ? lrErr : undefined}>
                {(p) => <Input {...p} inputMode="decimal" value={lr} onChange={(e) => setLr(e.target.value)} disabled={running} />}
              </FormField>
              <div className="flex gap-2">
                <Button className="flex-1" onClick={requestStart} loading={start.isPending} disabled={running || !dataset.data?.ready_to_train}>
                  <Play /> Start training
                </Button>
                <Button variant="danger" onClick={() => stop.mutate()} loading={stop.isPending} disabled={!running || s?.stopping}>
                  <Square /> Stop
                </Button>
              </div>
              {!dataset.isPending && !dataset.data?.ready_to_train && (
                <p className="text-xs text-warning">Collect images for at least 2 classes to enable training.</p>
              )}
            </CardBody>
          </Card>
        </div>

        <div className="space-y-6 lg:col-span-3">
          <Card>
            <CardHeader
              title="Training progress"
              icon={<Dumbbell />}
              action={
                s?.state === "training" || s?.state === "loading" ? (
                  <Badge tone="warning">{s.stopping ? "Stopping…" : s.state === "loading" ? "Preparing" : "Training"}</Badge>
                ) : s?.state === "done" ? (
                  <Badge tone="success">Finished</Badge>
                ) : s?.state === "error" ? (
                  <Badge tone="danger">Failed</Badge>
                ) : (
                  <Badge>Idle</Badge>
                )
              }
            />
            <CardBody className="space-y-4">
              {status.isPending ? (
                <Skeleton className="h-16 w-full" />
              ) : status.isError ? (
                <ErrorState error={status.error} title="Couldn't read the training status" onRetry={() => status.refetch()} />
              ) : (
                <>
                  <div aria-live="polite" className={cn("text-sm", s?.state === "error" ? "text-danger" : "text-muted-foreground")}>
                    {s?.state === "error" && <TriangleAlert className="mr-1.5 inline size-4 align-text-bottom" />}
                    {statusLine}
                  </div>
                  <ProgressBar value={progress} label="Training progress" indeterminate={s?.state === "loading" && !s.data.total} />
                  {s?.state === "error" && <p className="text-xs text-muted-foreground">Check the dataset (every class needs several images) and try again.</p>}
                  {s?.state === "done" && s.summary && (
                    <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-success/30 bg-success/[0.07] p-4">
                      <CheckCircle2 className="size-6 text-success" />
                      <div className="min-w-0 flex-1 text-sm">
                        <div className="font-medium">Model saved. Test accuracy {pct(s.summary.test_accuracy)}.</div>
                        <div className="text-xs text-muted-foreground">
                          {s.summary.labels.length} classes · test loss {s.summary.test_loss.toFixed(4)}
                        </div>
                      </div>
                      <Button asChild size="sm" variant="secondary">
                        <Link to="/app/model">See report</Link>
                      </Button>
                      <Button asChild size="sm">
                        <Link to="/app/recognize">
                          <Hand /> Try it live
                        </Link>
                      </Button>
                    </div>
                  )}
                </>
              )}
            </CardBody>
          </Card>
        </div>
      </div>

      <TrainingCharts history={s?.history} running={running} />

      <ConfirmModal
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Replace the current model?"
        description="A model is already trained. Training again overwrites it with the new best model when it finishes."
        confirmLabel="Train and replace"
        onConfirm={() => start.mutateAsync().catch(() => undefined)}
      />
    </div>
  );
}
