import { ArrowLeft, CalendarDays, Cpu, Download, FileText, Link2, Printer, ShieldCheck, Stethoscope, Timer, Wheat, Zap } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { Meter, SeverityBadge } from "@/components/agri/bits";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { toast } from "@/components/ui/Toast";
import { useBreadcrumb } from "@/components/ui/AppShell";
import { downloadFile, errorMessage } from "@/lib/api";
import { TREATMENT_TONE, pct } from "@/lib/disease";
import { useLang } from "@/lib/i18n";
import { useHealth, useResult } from "@/lib/queries";
import { formatDate } from "@/lib/utils";
import axios from "axios";

export default function Result() {
  const { id } = useParams();
  const { t } = useLang();
  const q = useResult(id);
  const health = useHealth();
  const [busy, setBusy] = useState<"csv" | "pdf" | null>(null);
  useBreadcrumb(q.data?.predicted_disease);

  async function download(format: "csv" | "pdf") {
    setBusy(format);
    try {
      await downloadFile(`/v1/history/${id}/export?format=${format}`, `agrivision-${id?.slice(0, 8)}.${format}`);
      toast.success(`${format.toUpperCase()} report downloaded`);
    } catch (e) {
      toast.error(`Couldn't export the ${format.toUpperCase()}: ${errorMessage(e)}`);
    } finally {
      setBusy(null);
    }
  }

  async function share() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      toast.success("Link copied. It opens for you when you are signed in.");
    } catch {
      toast.error("Your browser blocked copying. Copy the address bar link instead.");
    }
  }

  if (q.isError) {
    const notFound = axios.isAxiosError(q.error) && q.error.response?.status === 404;
    return notFound ? (
      <EmptyState
        icon={<FileText />}
        title="Result not found"
        description="This result doesn't exist or was deleted. Your other scans are in the history."
        action={
          <Button asChild>
            <Link to="/history">Open history</Link>
          </Button>
        }
      />
    ) : (
      <ErrorState error={q.error} title="Couldn't load this result" onRetry={() => q.refetch()} />
    );
  }

  if (q.isPending) {
    return (
      <div className="grid gap-5 lg:grid-cols-2" role="status" aria-label="Loading result">
        <Skeleton className="h-96 rounded-2xl" />
        <Skeleton className="h-96 rounded-2xl" />
      </div>
    );
  }

  const r = q.data;
  const info = r.disease_details;
  const heuristic = r.engine === "heuristic";

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" magnetic={false} className="-ml-2">
        <Link to="/history">
          <ArrowLeft /> Back to history
        </Link>
      </Button>

      <Stagger className="grid gap-5 lg:grid-cols-2">
        <StaggerItem>
          <Card className="overflow-hidden">
            <img src={r.image_url} alt={`Scanned leaf: ${r.predicted_disease}`} className="max-h-[26rem] w-full object-cover" />
            <div className="flex flex-wrap gap-x-5 gap-y-1 p-4 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                <CalendarDays className="size-3.5" aria-hidden /> {formatDate(r.created_at, true)}
              </span>
              <span className="inline-flex items-center gap-1.5 capitalize">
                <Wheat className="size-3.5" aria-hidden /> {r.crop_type}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Timer className="size-3.5" aria-hidden /> {r.latency_ms} ms
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Cpu className="size-3.5" aria-hidden /> {heuristic ? "Heuristic engine" : r.engine}
              </span>
            </div>
          </Card>
        </StaggerItem>

        <StaggerItem>
          <Card className="space-y-5 p-6">
            <div className="flex flex-wrap items-center gap-2">
              <SeverityBadge severity={r.severity} />
              {r.urgent && (
                <Badge tone="warning">
                  <Zap aria-hidden /> Urgent action
                </Badge>
              )}
            </div>
            <div>
              <h1 className="font-display text-3xl font-semibold tracking-tight text-balance">{r.predicted_disease}</h1>
              <p className="mt-1 text-sm text-muted-foreground">{info.description}</p>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-sm font-medium">
                <span>{heuristic ? "Heuristic score (not a calibrated probability)" : t("result.confidence", "AI confidence")}</span>
                <span className="tabular-nums">{pct(r.confidence, 2)}</span>
              </div>
              <Meter value={r.confidence} className="h-3" />
            </div>

            <div className="space-y-2">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t("result.top3", "Top-3 predictions")}</h2>
              <ul className="space-y-2">
                {r.top_3_predictions.map((p, i) => (
                  <li key={p.class} className="grid grid-cols-[1fr_auto] items-center gap-x-3 gap-y-1 text-sm sm:grid-cols-[1fr_8rem_auto]">
                    <span className={i === 0 ? "font-medium" : "text-muted-foreground"}>{p.disease}</span>
                    <Meter value={p.confidence} tone={i === 0 ? "primary" : "muted"} className="order-last col-span-2 sm:order-none sm:col-span-1" />
                    <b className="tabular-nums">{pct(p.confidence, 2)}</b>
                  </li>
                ))}
              </ul>
            </div>

            {heuristic && health.data && (
              <p className="rounded-xl border border-warning/30 bg-warning/[0.08] p-3 text-xs text-muted-foreground">
                <b className="text-foreground">Heuristic engine:</b> this diagnosis comes from leaf colour and texture cues, not a trained neural network. The
                score saturates near 97% for most photos, so it says little about how sure the engine is, and it can miss visible disease. Confirm with an agri
                officer before spraying.
              </p>
            )}

            <div className="flex flex-wrap gap-2 print:hidden">
              <Button variant="secondary" size="sm" magnetic={false} loading={busy === "csv"} onClick={() => download("csv")}>
                <Download /> CSV
              </Button>
              <Button variant="secondary" size="sm" magnetic={false} loading={busy === "pdf"} onClick={() => download("pdf")}>
                <FileText /> PDF
              </Button>
              <Button variant="secondary" size="sm" magnetic={false} onClick={() => window.print()}>
                <Printer /> Print
              </Button>
              <Button variant="secondary" size="sm" magnetic={false} onClick={share}>
                <Link2 /> Share
              </Button>
            </div>
          </Card>
        </StaggerItem>
      </Stagger>

      <div className="grid gap-5 md:grid-cols-2">
        <Card>
          <CardHeader title={t("result.symptoms", "Symptoms")} icon={<Stethoscope />} />
          <CardBody className="space-y-4 text-sm">
            <p>{info.symptoms}</p>
            <div>
              <h3 className="font-display font-semibold">{t("result.lifecycle", "Lifecycle")}</h3>
              <p className="mt-1 text-muted-foreground">{info.lifecycle}</p>
            </div>
            <div>
              <h3 className="font-display font-semibold">{t("result.prevention", "Prevention")}</h3>
              <p className="mt-1">{info.prevention}</p>
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title={t("result.treatments", "Recommended treatments")} icon={<ShieldCheck />} />
          <CardBody className="space-y-3">
            {info.treatments.map((tr) => (
              <div key={tr.type} className="rounded-xl border border-[var(--glass-border)] p-4">
                <div className="flex items-center gap-2">
                  <Badge tone={TREATMENT_TONE[tr.type]} className="uppercase">
                    {tr.type}
                  </Badge>
                  <b className="text-sm">{tr.name}</b>
                </div>
                <p className="mt-1.5 text-sm">{tr.detail}</p>
                <p className="mt-1 text-xs text-muted-foreground">Cost: {tr.cost}</p>
              </div>
            ))}
            <p className="rounded-xl border border-warning/30 bg-warning/[0.08] p-3 text-xs text-muted-foreground">
              Always do a patch test, wear protective equipment, and follow the label dose and waiting period. Consult your local agri officer to confirm.
            </p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
