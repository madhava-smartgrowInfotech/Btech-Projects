import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing, Copy, FlaskConical, Loader2, MessageSquareWarning, QrCode, RotateCcw } from "lucide-react";
import { toast } from "sonner";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { CardSkeleton, PageHeader } from "@/components/common/States";
import { api, apiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";

interface Samples {
  sms: { id: string; language: string; kind: string; text: string }[];
  qr: { id: string; kind: string; title: string; payload: string; image_url: string }[];
}

export default function Sandbox() {
  const { t, tx } = useI18n();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const samples = useQuery({ queryKey: ["sandbox", "samples"], queryFn: async () => (await api.get<Samples>("/sandbox/samples")).data });
  const incoming = useMutation({
    mutationFn: async (kind: "refund_trick" | "genuine") => (await api.post("/sandbox/incoming-collect", { kind })).data,
    onSuccess: () => {
      toast.success(t("sandbox.request_sent"));
      qc.invalidateQueries({ queryKey: ["collect"] });
      qc.invalidateQueries({ queryKey: ["badges"] });
    },
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });
  const reset = useMutation({
    mutationFn: async () => (await api.post("/sandbox/reset")).data,
    onSuccess: () => {
      toast.success(t("sandbox.reset_done"));
      logout();
      navigate("/login");
    },
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });

  return (
    <div className="space-y-5">
      <PageHeader title={t("nav.sandbox")} subtitle={t("sandbox.subtitle")} />
      <div className="flex items-start gap-3 rounded-2xl border border-caution/40 bg-caution-soft p-4 text-sm">
        <FlaskConical className="mt-0.5 h-5 w-5 shrink-0 text-caution" />
        <p>{t("sandbox.explain")}</p>
      </div>

      <section className="surface p-5">
        <h2 className="flex items-center gap-2 font-display text-base font-semibold">
          <BellRing className="h-4 w-4 text-primary" />
          {t("sandbox.collect_title")}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">{t("sandbox.collect_hint")}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button onClick={() => incoming.mutate("refund_trick")} disabled={incoming.isPending}>
            {incoming.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {t("sandbox.send_trick")}
          </Button>
          <Button variant="outline" onClick={() => incoming.mutate("genuine")} disabled={incoming.isPending}>
            {t("sandbox.send_genuine")}
          </Button>
          <Button variant="ghost" onClick={() => navigate("/app/collect")}>
            {t("sandbox.open_requests")}
          </Button>
        </div>
      </section>

      <section className="surface p-5">
        <h2 className="flex items-center gap-2 font-display text-base font-semibold">
          <QrCode className="h-4 w-4 text-primary" />
          {t("sandbox.qr_title")}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">{t("sandbox.qr_hint")}</p>
        {samples.isLoading ? (
          <CardSkeleton />
        ) : (
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {samples.data?.qr.map((q) => (
              <figure key={q.id} className="rounded-xl border p-3 text-center">
                <img src={q.image_url} alt={q.title} className="mx-auto aspect-square w-full max-w-[160px] rounded-lg bg-white p-1" />
                <figcaption className="mt-2 text-xs">
                  <span className={cn("mb-1 inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold", q.kind === "trick" ? "bg-danger-soft text-danger" : "bg-safe-soft text-safe")}>
                    {q.kind === "trick" ? t("scan.sample_trick") : t("scan.sample_genuine")}
                  </span>
                  <span className="block">{q.title}</span>
                </figcaption>
              </figure>
            ))}
          </div>
        )}
      </section>

      <section className="surface p-5">
        <h2 className="flex items-center gap-2 font-display text-base font-semibold">
          <MessageSquareWarning className="h-4 w-4 text-primary" />
          {t("sandbox.sms_title")}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">{t("sandbox.sms_hint")}</p>
        <ul className="mt-3 space-y-2">
          {samples.data?.sms.map((s) => (
            <li key={s.id} className="flex items-start gap-3 rounded-xl border p-3 text-sm">
              <span className={cn("mt-0.5 shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase", s.kind === "scam" ? "bg-danger-soft text-danger" : "bg-safe-soft text-safe")}>{s.language}</span>
              <span className="min-w-0 flex-1 break-words">{s.text}</span>
              <Button
                variant="ghost"
                size="icon"
                aria-label={t("common.copy")}
                onClick={() => navigator.clipboard?.writeText(s.text).then(() => toast.success(t("common.copied")))}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </li>
          ))}
        </ul>
      </section>

      {user?.role === "admin" && (
        <section className="surface border-danger/30 p-5">
          <h2 className="flex items-center gap-2 font-display text-base font-semibold">
            <RotateCcw className="h-4 w-4 text-danger" />
            {t("sandbox.reset_title")}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">{t("sandbox.reset_hint")}</p>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" className="mt-3 text-danger" disabled={reset.isPending}>
                {reset.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {t("sandbox.reset")}
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>{t("sandbox.reset_confirm")}</AlertDialogTitle>
                <AlertDialogDescription>{t("sandbox.reset_hint")}</AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>{t("common.cancel")}</AlertDialogCancel>
                <AlertDialogAction onClick={() => reset.mutate()}>{t("sandbox.reset")}</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </section>
      )}
    </div>
  );
}
