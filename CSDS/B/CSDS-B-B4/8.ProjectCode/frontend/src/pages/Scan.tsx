import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { Camera, CameraOff, CheckCircle2, ImageUp, IndianRupee, Loader2, QrCode, ShieldAlert } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader } from "@/components/common/States";
import { HighlightedText } from "@/components/risk/HighlightedText";
import { GuideButton, SpeakButton } from "@/components/voice/SpeakButton";
import { api, apiError } from "@/lib/api";
import { formatINR } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import type { Payment, QrResult } from "@/lib/types";
import { deviceType } from "@/pages/Send";

interface QrSample {
  id: string;
  kind: "genuine" | "trick";
  title: string;
  payload: string;
  image_url: string;
}

function CameraScanner({ onDecode }: { onDecode: (text: string) => void }) {
  const { t } = useI18n();
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const ref = useRef<import("html5-qrcode").Html5Qrcode | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!window.isSecureContext) {
        setError(t("scan.need_https"));
        return;
      }
      const { Html5Qrcode } = await import("html5-qrcode");
      if (cancelled) return;
      const scanner = new Html5Qrcode("qr-reader", { verbose: false });
      ref.current = scanner;
      try {
        await scanner.start({ facingMode: "environment" }, { fps: 10, qrbox: { width: 230, height: 230 } }, (text) => {
          onDecode(text);
          scanner.stop().catch(() => undefined);
          setRunning(false);
        }, () => undefined);
        setRunning(true);
      } catch (e) {
        setError(e instanceof Error ? e.message : t("scan.camera_error"));
      }
    })();
    return () => {
      cancelled = true;
      ref.current?.isScanning && ref.current.stop().catch(() => undefined);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <div id="qr-reader" className="mx-auto aspect-square w-full max-w-sm overflow-hidden rounded-2xl bg-muted" />
      {error ? (
        <p className="mt-3 flex items-start gap-2 text-sm text-muted-foreground">
          <CameraOff className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </p>
      ) : (
        <p className="mt-3 text-center text-sm text-muted-foreground">{running ? t("scan.point_camera") : t("common.loading")}</p>
      )}
    </div>
  );
}

export default function Scan() {
  const { t, tx } = useI18n();
  const navigate = useNavigate();
  const [result, setResult] = useState<QrResult | null>(null);
  const [amount, setAmount] = useState("");
  const [tab, setTab] = useState("camera");
  const samples = useQuery({ queryKey: ["sandbox", "samples"], queryFn: async () => (await api.get<{ qr: QrSample[] }>("/sandbox/samples")).data });

  const parse = useMutation({
    mutationFn: async (payload: string) => (await api.post<QrResult>("/qr/parse", { payload })).data,
    onSuccess: (r) => {
      setResult(r);
      setAmount(r.amount ? String(r.amount) : "");
    },
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });

  const assess = useMutation({
    mutationFn: async () =>
      (await api.post<Payment>("/payments/assess", { upi_id: result!.payee_upi_id, amount: Number(amount), channel: "qr", qr_payload: result!.raw, note: result!.note, device: deviceType() })).data,
    onSuccess: (p) => navigate(`/app/pay/${p.id}`),
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });

  const upload = async (file: File) => {
    try {
      const { Html5Qrcode } = await import("html5-qrcode");
      const reader = new Html5Qrcode("qr-file-reader", { verbose: false });
      const text = await reader.scanFile(file, false);
      parse.mutate(text);
    } catch {
      toast.error(t("scan.no_code_in_image"));
    }
  };

  const trick = result && result.flags.some((f) => ["scan_to_receive", "name_mismatch", "receive_words", "qr_is_link"].includes(f));
  const amountOk = Number(amount) > 0 && Number(amount) <= 100000;

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title={t("nav.scan")} subtitle={t("scan.subtitle")} actions={<GuideButton screen="scan" />} />
      <div id="qr-file-reader" className="hidden" />

      {!result ? (
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="camera">
              <Camera className="mr-1.5 h-4 w-4" />
              {t("scan.tab.camera")}
            </TabsTrigger>
            <TabsTrigger value="upload">
              <ImageUp className="mr-1.5 h-4 w-4" />
              {t("scan.tab.upload")}
            </TabsTrigger>
            <TabsTrigger value="samples">
              <QrCode className="mr-1.5 h-4 w-4" />
              {t("scan.tab.samples")}
            </TabsTrigger>
          </TabsList>
          <TabsContent value="camera" className="surface p-4">
            {tab === "camera" && <CameraScanner onDecode={(text) => parse.mutate(text)} />}
          </TabsContent>
          <TabsContent value="upload" className="surface p-6">
            <label className="flex cursor-pointer flex-col items-center gap-3 rounded-2xl border-2 border-dashed p-10 text-center transition hover:border-primary/50">
              <ImageUp className="h-8 w-8 text-muted-foreground" />
              <span className="font-medium">{t("scan.upload_title")}</span>
              <span className="text-sm text-muted-foreground">{t("scan.upload_hint")}</span>
              <input type="file" accept="image/*" className="sr-only" onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
            </label>
          </TabsContent>
          <TabsContent value="samples" className="space-y-3">
            <p className="text-sm text-muted-foreground">{t("scan.samples_hint")}</p>
            <div className="grid gap-3 sm:grid-cols-2">
              {samples.data?.qr.map((s) => (
                <button key={s.id} onClick={() => parse.mutate(s.payload)} className="surface flex items-center gap-3 p-3 text-left transition hover:shadow-lift">
                  <img src={s.image_url} alt="" className="h-16 w-16 rounded-lg border bg-white p-1" loading="lazy" />
                  <span className="min-w-0">
                    <span className="block text-sm font-medium">{s.title}</span>
                    <span className="text-xs text-muted-foreground">{s.kind === "trick" ? t("scan.sample_trick") : t("scan.sample_genuine")}</span>
                  </span>
                </button>
              ))}
            </div>
          </TabsContent>
          {parse.isPending && (
            <p className="mt-3 flex items-center justify-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              {t("scan.checking")}
            </p>
          )}
        </Tabs>
      ) : (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          {trick ? (
            <div className="rounded-2xl border-2 border-danger bg-danger-soft p-5">
              <p className="flex items-center gap-2 font-display text-lg font-semibold text-danger">
                <ShieldAlert className="h-5 w-5" />
                {t("qr.guard_title")}
              </p>
              <ul className="mt-2 list-inside list-disc space-y-1 text-sm">
                {result.flags.map((f) => (
                  <li key={f}>{tx(`qr.flag.${f}`, f, { name: result.payee_name_in_qr ?? "", registered: result.registered_name ?? "" })}</li>
                ))}
              </ul>
              <div className="mt-3">
                <SpeakButton source={{ kind: "qr-trick" }} autoPlay />
              </div>
            </div>
          ) : result.valid ? (
            <div className="flex items-center gap-2 rounded-2xl border border-safe/30 bg-safe-soft p-4 text-sm text-safe">
              <CheckCircle2 className="h-5 w-5" />
              {t("scan.looks_ok")}
            </div>
          ) : (
            <div className="rounded-2xl border bg-muted p-4 text-sm">{tx(`qr.flag.${result.flags[0] ?? "not_upi"}`, t("scan.not_upi"))}</div>
          )}

          {result.valid && (
            <div className="surface space-y-4 p-5">
              <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
                <dt className="text-muted-foreground">{t("scan.pays_to")}</dt>
                <dd className="font-medium">
                  {result.registered_name} <span className="font-mono text-xs text-muted-foreground">{result.payee_upi_id}</span>
                </dd>
                {result.payee_name_in_qr && (
                  <>
                    <dt className="text-muted-foreground">{t("scan.name_on_code")}</dt>
                    <dd>{result.payee_name_in_qr}</dd>
                  </>
                )}
                {result.note && (
                  <>
                    <dt className="text-muted-foreground">{t("scan.note")}</dt>
                    <dd>
                      <HighlightedText text={result.note} highlights={result.note_analysis?.highlights ?? []} />
                    </dd>
                  </>
                )}
              </dl>
              <div className="space-y-2">
                <Label htmlFor="qr-amount">{t("send.amount")}</Label>
                <div className="relative">
                  <IndianRupee className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                  <Input id="qr-amount" inputMode="decimal" className="h-14 pl-10 font-display text-2xl tabular" value={amount} onChange={(e) => setAmount(e.target.value.replace(/[^\d.]/g, ""))} readOnly={!!result.amount} />
                </div>
                {result.amount && <p className="text-xs text-muted-foreground">{t("scan.preset_amount", { amount: formatINR(result.amount) })}</p>}
              </div>
              <div className="flex flex-col gap-2 sm:flex-row">
                <Button variant="outline" size="lg" className="flex-1" onClick={() => setResult(null)}>
                  {t("scan.scan_again")}
                </Button>
                <Button size="lg" className="flex-1" disabled={!amountOk || assess.isPending || result.is_self} onClick={() => assess.mutate()}>
                  {assess.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {t("send.check_and_pay")}
                </Button>
              </div>
            </div>
          )}
          {!result.valid && (
            <Button variant="outline" onClick={() => setResult(null)}>
              {t("scan.scan_again")}
            </Button>
          )}
        </motion.div>
      )}
    </div>
  );
}
