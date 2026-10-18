import { useQueryClient } from "@tanstack/react-query";
import { Camera, CameraOff, Film, ImageIcon, Images, Lightbulb, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";

import { CameraView } from "@/components/camera/CameraView";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, ProgressBar, Skeleton } from "@/components/ui/Feedback";
import { FormField, Input } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { Select } from "@/components/ui/Select";
import { toast } from "@/components/ui/Toast";
import { endpoints, errorMessage } from "@/lib/api";
import { useCamera } from "@/lib/camera";
import { classLabel } from "@/lib/format";
import { keys, useConfig, useDataset, useImages } from "@/lib/queries";
import { cn } from "@/lib/utils";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export default function Collect() {
  const cam = useCamera();
  const { grab, running } = cam;
  const qc = useQueryClient();
  const config = useConfig();
  const dataset = useDataset();
  const [cls, setCls] = useState("A");
  const [burstText, setBurstText] = useState("60");
  const [burst, setBurst] = useState<{ done: number; total: number } | null>(null);
  const [burstNote, setBurstNote] = useState<string | null>(null);
  const [mask, setMask] = useState<string | null>(null);
  const [liveCount, setLiveCount] = useState<Record<string, number>>({});
  const [capturing, setCapturing] = useState(false);
  const cancelRef = useRef(false);
  const busyRef = useRef(false);
  const images = useImages(cls, 24);

  const count = liveCount[cls] ?? dataset.data?.counts[cls] ?? 0;
  const burstN = Number(burstText);
  const burstError =
    !Number.isInteger(burstN) || burstN < 1 || burstN > 1000 ? "Enter a whole number from 1 to 1000." : undefined;

  // live segmentation preview (about 3 per second, paused while a capture is in flight)
  useEffect(() => {
    if (!running) {
      setMask(null);
      return;
    }
    let alive = true;
    (async () => {
      while (alive) {
        if (!busyRef.current) {
          const blob = await grab(0.7);
          if (blob && alive && !busyRef.current) {
            try {
              setMask((await endpoints.preview(blob)).mask);
            } catch {
              /* preview is best-effort; capture reports its own errors */
            }
          }
        }
        await sleep(350);
      }
    })();
    return () => {
      alive = false;
    };
  }, [running, grab]);

  function refresh() {
    qc.invalidateQueries({ queryKey: keys.dataset });
    qc.invalidateQueries({ queryKey: keys.images(cls) });
    qc.invalidateQueries({ queryKey: keys.model });
  }

  async function captureOne() {
    if (!running) {
      toast.warning("Start the camera first");
      return;
    }
    busyRef.current = true;
    setCapturing(true);
    try {
      const blob = await grab(0.92);
      if (!blob) throw new Error("The camera has no frame yet. Wait a moment and try again.");
      const r = await endpoints.collect(cls, blob);
      setLiveCount((c) => ({ ...c, [cls]: r.count }));
      setMask(r.mask);
      toast.success(`Saved 1 image for ${classLabel(cls)}`, { description: `${r.count} collected for this class.` });
      refresh();
    } catch (e) {
      toast.error("Couldn't save the image", { description: errorMessage(e) });
    } finally {
      busyRef.current = false;
      setCapturing(false);
    }
  }

  async function startBurst() {
    if (!running) {
      toast.warning("Start the camera first");
      return;
    }
    if (burstError) return;
    const total = burstN;
    cancelRef.current = false;
    busyRef.current = true;
    setCapturing(true);
    setBurstNote(null);
    setBurst({ done: 0, total });
    let done = 0;
    try {
      while (done < total && !cancelRef.current) {
        const blob = await grab(0.92);
        if (blob) {
          const r = await endpoints.collect(cls, blob);
          done += 1;
          setBurst({ done, total });
          setLiveCount((c) => ({ ...c, [cls]: r.count }));
          setMask(r.mask);
        }
        await sleep(config.data?.capture_delay_ms ?? 60);
      }
      setBurstNote(cancelRef.current ? `Stopped after ${done} of ${total} images.` : "Done!");
      if (!cancelRef.current) toast.success(`Captured ${done} images for ${classLabel(cls)}`);
    } catch (e) {
      setBurstNote(`Stopped after ${done} of ${total}: ${errorMessage(e)}`);
      toast.error("Burst capture failed", { description: errorMessage(e) });
    } finally {
      busyRef.current = false;
      setCapturing(false);
      setBurst(null);
      refresh();
    }
  }

  const classes = config.data?.classes ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Dataset"
        title="Collect data"
        description="Capture hand images for each letter. They are cropped to the cyan box and saved to the data folder, one folder per class."
        actions={
          running ? (
            <Button variant="secondary" onClick={() => (cancelRef.current = true, cam.stop())}>
              <CameraOff /> Stop camera
            </Button>
          ) : (
            <Button onClick={() => cam.start()} loading={cam.state === "starting"}>
              <Camera /> Start camera
            </Button>
          )
        }
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
        <Card className="lg:col-span-3">
          <CardHeader title="Camera" icon={<Camera />} action={running ? <Badge tone="success">Camera running</Badge> : <Badge>Camera stopped</Badge>} />
          <CardBody>
            <CameraView videoRef={cam.videoRef} state={cam.state} error={cam.error} roi={config.data?.roi} onStart={() => cam.start()} />
          </CardBody>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader title="Capture settings" icon={<ImageIcon />} />
          <CardBody className="space-y-4">
            <FormField label="Class" hint={`${count.toLocaleString("en-US")} image${count === 1 ? "" : "s"} collected for ${classLabel(cls)}`}>
              {(p) => (
                <Select
                  {...p}
                  value={cls}
                  onValueChange={setCls}
                  disabled={capturing}
                  options={classes.map((c) => ({ value: c, label: `${classLabel(c)} · ${liveCount[c] ?? dataset.data?.counts[c] ?? 0}` }))}
                />
              )}
            </FormField>

            <div className="flex items-center gap-3">
              <div className="grid size-24 shrink-0 place-items-center overflow-hidden rounded-2xl border border-[var(--glass-border)] bg-black">
                {mask ? (
                  <img src={mask} alt="Segmentation preview of the hand" className="size-full object-contain" />
                ) : (
                  <span className="px-2 text-center text-[11px] text-slate-400">Mask preview</span>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                This white-on-black silhouette is what the network learns from. If it looks noisy, simplify the background or add light.
              </p>
            </div>

            <Button className="w-full" onClick={captureOne} loading={capturing && !burst}>
              <Camera /> Capture 1 image
            </Button>

            <div className="space-y-2">
              <div className="flex items-start gap-2">
                <FormField label="Burst size" error={burstError} className="w-28">
                  {(p) => (
                    <Input {...p} inputMode="numeric" value={burstText} onChange={(e) => setBurstText(e.target.value)} disabled={capturing} />
                  )}
                </FormField>
                <div className="flex-1 pt-[26px]">
                  {burst ? (
                    <Button
                      className="w-full"
                      variant="danger"
                      onClick={() => {
                        cancelRef.current = true;
                      }}
                    >
                      <Square /> Stop
                    </Button>
                  ) : (
                    <Button className="w-full" variant="secondary" onClick={startBurst} disabled={Boolean(burstError) || capturing}>
                      <Film /> Burst capture
                    </Button>
                  )}
                </div>
              </div>
              {burst && (
                <div className="space-y-1" aria-live="polite">
                  <ProgressBar value={(burst.done / burst.total) * 100} label="Burst progress" />
                  <p className="text-xs text-muted-foreground tabular-nums">
                    {burst.done} / {burst.total} images
                  </p>
                </div>
              )}
              {!burst && burstNote && (
                <p className={cn("text-xs", burstNote === "Done!" ? "text-success" : "text-muted-foreground")} role="status">
                  {burstNote}
                </p>
              )}
            </div>
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader
            title={`Recent captures · ${classLabel(cls)}`}
            icon={<Images />}
            description={images.data ? `${images.data.total.toLocaleString("en-US")} saved, newest first` : undefined}
          />
          <CardBody>
            {images.isPending ? (
              <div className="grid grid-cols-4 gap-2 sm:grid-cols-6" role="status" aria-label="Loading images">
                {Array.from({ length: 12 }).map((_, i) => (
                  <Skeleton key={i} className="aspect-square" />
                ))}
              </div>
            ) : images.isError ? (
              <ErrorState error={images.error} title="Couldn't load the images" onRetry={() => images.refetch()} />
            ) : images.data.images.length === 0 ? (
              <EmptyState
                icon={<Images />}
                title={`No images for ${classLabel(cls)} yet`}
                description="Start the camera, place your hand in the cyan box and capture. Or drop an existing dataset into data/<class>/ (see the README)."
                action={
                  !running && (
                    <Button onClick={() => cam.start()}>
                      <Camera /> Start camera
                    </Button>
                  )
                }
              />
            ) : (
              <ul className="grid grid-cols-4 gap-2 sm:grid-cols-6">
                {images.data.images.map((img) => (
                  <li key={img.name} className="aspect-square overflow-hidden rounded-xl border border-[var(--glass-border)] bg-black">
                    <img src={img.url} alt={`${classLabel(cls)} sample`} loading="lazy" className="size-full object-cover" />
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader title="Tips" icon={<Lightbulb />} />
          <CardBody className="space-y-2 text-sm text-muted-foreground">
            <p>Keep a plain, uncluttered background and good, even lighting behind your hand so the silhouette is clean.</p>
            <p>Collect about 150-250 images per class from slightly varied angles and distances.</p>
            <p>You need at least 2 classes with images to train.</p>
            <Button asChild variant="secondary" size="sm" className="mt-2">
              <Link to="/app/train">Continue to training</Link>
            </Button>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader title="Dataset coverage" description="Click a class to capture it. Counts update as you collect." />
        <CardBody>
          {dataset.isPending ? (
            <Skeleton className="h-24 w-full" />
          ) : (
            <ul className="grid grid-cols-[repeat(auto-fill,minmax(4.25rem,1fr))] gap-2">
              {classes.map((c) => {
                const n = liveCount[c] ?? dataset.data?.counts[c] ?? 0;
                return (
                  <li key={c}>
                    <button
                      type="button"
                      onClick={() => setCls(c)}
                      disabled={capturing}
                      aria-pressed={c === cls}
                      aria-label={`${classLabel(c)}: ${n} images`}
                      className={cn(
                        "flex w-full flex-col items-center rounded-xl border px-1 py-2 transition-colors disabled:opacity-60",
                        c === cls ? "border-transparent bg-grad-primary text-white" : "border-[var(--glass-border)] bg-[var(--glass)] hover:bg-[var(--glass-hover)]",
                        c !== cls && n === 0 && "text-muted-foreground",
                      )}
                    >
                      <span className="font-display text-base font-semibold">{c.length > 1 ? classLabel(c) : c}</span>
                      <span className="text-[11px] tabular-nums opacity-80">{n}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
