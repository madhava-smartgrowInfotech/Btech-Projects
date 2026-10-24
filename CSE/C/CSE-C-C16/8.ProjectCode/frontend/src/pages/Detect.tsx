import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Camera, Focus, ScanSearch, Sun, Sparkles, Wheat } from "lucide-react";
import { useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";

import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { FormField } from "@/components/ui/Field";
import { ProgressBar } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { FileDrop } from "@/components/ui/FileDrop";
import { Select } from "@/components/ui/Select";
import { toast } from "@/components/ui/Toast";
import { api, CROP_OPTIONS, errorMessage, type DetectResponse } from "@/lib/api";
import { useLang } from "@/lib/i18n";
import { useHealth } from "@/lib/queries";
import { formatBytes } from "@/lib/utils";

const MAX_BYTES = 10 * 1024 * 1024;
const EXT = ["jpg", "jpeg", "png", "webp"];

function validate(f: File): string | null {
  const ext = f.name.split(".").pop()?.toLowerCase() ?? "";
  if (!EXT.includes(ext)) return "Image must be JPG, PNG, JPEG or WEBP.";
  if (f.size > MAX_BYTES) return `That image is ${formatBytes(f.size)}. The limit is 10 MB.`;
  return null;
}

const TIPS = [
  { icon: Focus, title: "Fill the frame", text: "One leaf, plain background." },
  { icon: Sun, title: "Use daylight", text: "Natural light, no flash glare." },
  { icon: ScanSearch, title: "Keep it sharp", text: "Spots or mould clearly visible, not blurry." },
];

export default function Detect() {
  const { t } = useLang();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [params] = useSearchParams();
  const initialCrop = params.get("crop") ?? "tomato";
  const [crop, setCrop] = useState(CROP_OPTIONS.includes(initialCrop as (typeof CROP_OPTIONS)[number]) ? initialCrop : "tomato");
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const cameraRef = useRef<HTMLInputElement>(null);
  const health = useHealth();

  const mutation = useMutation({
    mutationFn: async () => {
      const body = new FormData();
      body.append("image", file as File);
      body.append("crop_type", crop);
      setProgress(0);
      const res = await api.post<DetectResponse>("/v1/detect/upload", body, {
        timeout: 120_000,
        onUploadProgress: (e) => e.total && setProgress(Math.round((e.loaded / e.total) * 100)),
      });
      return res.data;
    },
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["history"] });
      void queryClient.invalidateQueries({ queryKey: ["analytics"] });
      toast.success(`Diagnosis ready: ${data.predicted_disease}`);
      navigate(`/result/${data.result_id}`);
    },
  });

  const busy = mutation.isPending;
  const uploading = busy && progress < 100;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        eyebrow="Diagnose"
        title={t("detect.title", "Detect plant disease")}
        description="Upload a clear photo of a single leaf in daylight. The result usually arrives in about a second."
      />

      <Card>
        <CardHeader title="Leaf photo" icon={<Camera />} description="JPG, PNG, JPEG or WEBP, up to 10 MB." />
        <CardBody className="space-y-5">
          <FormField label={t("detect.crop", "Crop type")} hint="Choose the crop so only its diseases are considered. Pick “general” if unsure.">
            {(p) => (
              <Select
                id={p.id}
                aria-describedby={p["aria-describedby"]}
                aria-label="Crop type"
                icon={<Wheat />}
                value={crop}
                onValueChange={setCrop}
                disabled={busy}
                options={CROP_OPTIONS.map((c) => ({ value: c, label: c[0].toUpperCase() + c.slice(1) }))}
              />
            )}
          </FormField>

          <FileDrop
            file={file}
            onFile={setFile}
            onPick={() => mutation.reset()}
            accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
            validate={validate}
            disabled={busy}
            title="Drag and drop a leaf image here, or click to browse"
            hint="JPG / PNG / JPEG / WEBP · max 10 MB"
          >
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="secondary" size="sm" magnetic={false} onClick={() => cameraRef.current?.click()} disabled={busy}>
                <Camera /> {t("detect.camera", "Use camera")}
              </Button>
            </div>
          </FileDrop>
          {/* phone camera: opens the rear camera directly */}
          <input
            ref={cameraRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="sr-only"
            tabIndex={-1}
            aria-label="Take a photo with the camera"
            onChange={(e) => {
              const f = e.target.files?.[0];
              e.target.value = "";
              if (!f) return;
              const problem = validate(f);
              if (problem) toast.error(problem);
              else {
                mutation.reset();
                setFile(f);
              }
            }}
          />

          {!file && (
            <p className="rounded-xl border border-dashed border-[var(--glass-border)] px-4 py-3 text-sm text-muted-foreground">
              No file chosen yet. Add a leaf photo to enable the diagnosis.
            </p>
          )}

          {busy && (
            <div className="space-y-2" role="status" aria-live="polite">
              <ProgressBar value={uploading ? progress : 100} indeterminate={!uploading} label="Analysing leaf" />
              <p className="flex items-center gap-1.5 text-xs font-medium text-violet-ink">
                <Sparkles className="size-3.5" aria-hidden /> {uploading ? `Uploading ${progress}%…` : "Analysing the leaf…"}
              </p>
            </div>
          )}

          {mutation.isError && (
            <div role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.07] p-3 text-sm">
              <p className="font-medium text-danger">The diagnosis failed.</p>
              <p className="text-muted-foreground">{errorMessage(mutation.error)}</p>
              <p className="mt-1 text-xs text-muted-foreground">Check the photo is a real image under 10 MB, then press the button again.</p>
            </div>
          )}

          <Button size="lg" className="w-full" disabled={!file} loading={busy} onClick={() => mutation.mutate()}>
            <ScanSearch /> {t("detect.go", "Diagnose now")}
          </Button>
          {health.data && !health.data.trained_model && (
            <p className="text-center text-xs text-muted-foreground">
              Diagnosis uses the colour/texture heuristic engine because no trained CNN is installed. Treat it as a first screen.
            </p>
          )}
        </CardBody>
      </Card>

      <Stagger className="grid gap-3 sm:grid-cols-3">
        {TIPS.map(({ icon: Icon, title, text }) => (
          <StaggerItem key={title}>
            <Card className="flex h-full gap-3 p-4">
              <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-grad-soft text-violet-ink">
                <Icon className="size-4" />
              </span>
              <div className="text-sm">
                <div className="font-medium">{title}</div>
                <div className="text-muted-foreground">{text}</div>
              </div>
            </Card>
          </StaggerItem>
        ))}
      </Stagger>
    </div>
  );
}
