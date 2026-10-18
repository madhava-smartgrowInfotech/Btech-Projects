import { useQueryClient } from "@tanstack/react-query";
import { Camera, CameraOff, Delete, Eraser, Hand, Keyboard, Space, Volume2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router";

import { CameraView } from "@/components/camera/CameraView";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, ProgressBar, Skeleton } from "@/components/ui/Feedback";
import { Textarea } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { toast } from "@/components/ui/Toast";
import { endpoints, errorMessage, httpStatus } from "@/lib/api";
import { useCamera } from "@/lib/camera";
import { classLabel } from "@/lib/format";
import { keys, useConfig, useHealth } from "@/lib/queries";
import type { RecognizeResult } from "@/lib/types";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export default function Recognize() {
  const cam = useCamera();
  const { grab, running } = cam;
  const qc = useQueryClient();
  const config = useConfig();
  const health = useHealth();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [modelReady, setModelReady] = useState(false);
  const [result, setResult] = useState<RecognizeResult | null>(null);
  const [sentence, setSentence] = useState("");
  const [loopError, setLoopError] = useState<string | null>(null);
  const [speaking, setSpeaking] = useState(false);
  const sessionRef = useRef<string | null>(null);
  sessionRef.current = sessionId;

  const commit = useCallback((label: string) => {
    setSentence((s) => (label === "space" ? `${s} ` : label === "del" ? s.slice(0, -1) : s + label));
  }, []);

  async function startCamera() {
    const ok = await cam.start();
    if (!ok) return;
    try {
      // like the desktop app: (re)load the model when the camera starts
      let ready = health.data?.model_loaded ?? false;
      if (!ready && health.data?.model_file) ready = (await endpoints.reload()).model_loaded;
      if (ready) setSessionId((await endpoints.session()).session_id);
      setModelReady(ready);
      qc.invalidateQueries({ queryKey: keys.health });
    } catch (e) {
      setLoopError(errorMessage(e));
    }
  }

  function stopCamera() {
    cam.stop();
    setSessionId(null);
    setModelReady(false);
    setResult(null);
  }

  // frame loop: grab -> POST -> show prediction (about 10-15 fps, one request at a time)
  useEffect(() => {
    if (!running || !sessionId || !modelReady) return;
    let alive = true;
    (async () => {
      while (alive) {
        const t0 = performance.now();
        const blob = await grab(0.8);
        if (!blob) {
          await sleep(120);
          continue;
        }
        try {
          const r = await endpoints.recognize(blob, sessionRef.current ?? sessionId);
          if (!alive) break;
          setResult(r);
          setLoopError(null);
          if (r.committed) commit(r.committed);
        } catch (e) {
          if (!alive) break;
          if (httpStatus(e) === 404) {
            try {
              setSessionId((await endpoints.session()).session_id);
            } catch {
              /* reported below on the next failure */
            }
          }
          setLoopError(errorMessage(e));
          await sleep(1000);
        }
        const dt = performance.now() - t0;
        if (dt < 60) await sleep(60 - dt);
      }
    })();
    return () => {
      alive = false;
    };
  }, [running, grab, sessionId, modelReady, commit]);

  async function speak() {
    if (!sentence.trim()) {
      toast.info("Nothing to speak yet", { description: "Hold a sign steady or type some letters first." });
      return;
    }
    setSpeaking(true);
    try {
      await endpoints.speak(sentence);
      toast.success("Speaking your sentence");
    } catch (e) {
      if (httpStatus(e) === 400) toast.error(errorMessage(e));
      else if ("speechSynthesis" in window) {
        window.speechSynthesis.speak(new SpeechSynthesisUtterance(sentence));
        toast.info("Using the browser voice", { description: "The server voice was unavailable." });
      } else toast.error("Couldn't speak the sentence", { description: errorMessage(e) });
    } finally {
      setSpeaking(false);
    }
  }

  const noModel = health.data && !health.data.model_file && !health.data.model_loaded;
  const stable = result?.stable_label ?? "nothing";
  const shown = stable === "nothing" ? "—" : stable === "space" ? "␣" : stable === "del" ? "⌫" : stable;
  const confidence = result ? Math.round(result.confidence * 100) : 0;
  const threshold = config.data ? Math.round(config.data.thresholds.confidence * 100) : 75;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Live"
        title="Recognize signs"
        description="Show a letter inside the cyan box. Hold it steady and it is typed into your sentence."
        actions={
          cam.running ? (
            <Button variant="secondary" onClick={stopCamera}>
              <CameraOff /> Stop camera
            </Button>
          ) : (
            <Button onClick={startCamera} loading={cam.state === "starting"}>
              <Camera /> Start camera
            </Button>
          )
        }
      />

      {health.isError && (
        <ErrorState error={health.error} title="The SignSpeak server isn't answering" hint="Start it with run.bat, then reload this page." onRetry={() => health.refetch()} />
      )}

      {noModel && (
        <div role="status" className="glass flex flex-wrap items-center gap-3 rounded-2xl border-warning/40 px-4 py-3 text-sm">
          <Badge tone="warning">No trained model</Badge>
          <span className="min-w-0 flex-1 text-muted-foreground">
            The camera works, but nothing can be recognised until a model is trained. Collect images, then train.
          </span>
          <Button asChild size="sm" variant="secondary">
            <Link to="/app/train">Go to Train</Link>
          </Button>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="space-y-3 lg:col-span-3">
          <Card>
            <CardHeader
              title="Live camera"
              icon={<Camera />}
              action={cam.running ? <Badge tone="success">Camera running</Badge> : <Badge>Camera stopped</Badge>}
            />
            <CardBody className="space-y-3">
              <CameraView videoRef={cam.videoRef} state={cam.state} error={cam.error} roi={config.data?.roi} onStart={startCamera} />
              {loopError && cam.running && (
                <p role="alert" className="text-sm text-danger">
                  {loopError}
                </p>
              )}
              <p className="text-xs text-muted-foreground">
                A letter counts after about {config.data?.thresholds.stable_frames ?? 18} steady frames at {threshold}% confidence or more. A plain
                background and even light give the cleanest silhouette.
              </p>
            </CardBody>
          </Card>
        </div>

        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader title="Prediction" icon={<Hand />} />
            <CardBody className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="grid size-28 shrink-0 place-items-center overflow-hidden rounded-2xl border border-[var(--glass-border)] bg-black">
                  {result ? (
                    <img src={result.mask} alt="Segmented hand mask the network sees" className="size-full object-contain" />
                  ) : (
                    <span className="px-2 text-center text-[11px] text-slate-400">Mask appears when the camera runs</span>
                  )}
                </div>
                <div className="min-w-0 flex-1 text-center">
                  <div
                    className="font-display text-6xl font-bold leading-none text-gradient"
                    aria-live="polite"
                    aria-label={result ? `Predicted ${classLabel(stable)}` : "No prediction yet"}
                  >
                    {shown}
                  </div>
                  <div className="mt-1 text-xs text-muted-foreground">{result ? classLabel(stable) : "waiting"}</div>
                </div>
              </div>
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Confidence</span>
                  <span className="tabular-nums">{result ? `${confidence}%` : "-"}</span>
                </div>
                <ProgressBar value={confidence} label="Confidence" />
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Sentence" icon={<Keyboard />} description="Edit it by hand too." />
            <CardBody className="space-y-3">
              <Textarea
                aria-label="Sentence"
                value={sentence}
                onChange={(e) => setSentence(e.target.value.toUpperCase())}
                placeholder="Signed letters appear here…"
                className="min-h-24 font-display text-lg tracking-wider"
              />
              <div className="flex flex-wrap gap-2">
                <Button variant="secondary" size="sm" onClick={() => setSentence((s) => `${s} `)}>
                  <Space /> Space
                </Button>
                <Button variant="secondary" size="sm" onClick={() => setSentence((s) => s.slice(0, -1))} disabled={!sentence}>
                  <Delete /> Back
                </Button>
                <Button variant="danger" size="sm" onClick={() => setSentence("")} disabled={!sentence}>
                  <Eraser /> Clear
                </Button>
              </div>
              <Button className="w-full" onClick={speak} loading={speaking}>
                <Volume2 /> Speak sentence
              </Button>
            </CardBody>
          </Card>
        </div>
      </div>

      {!config.data && config.isPending && <Skeleton className="h-4 w-48" />}
      {!cam.running && cam.state === "idle" && !noModel && !health.isError && (
        <EmptyState
          icon={<Hand />}
          title="Ready when you are"
          description="Press Start camera, put your hand inside the cyan box and sign a letter. The model is loaded on the server for you."
          action={
            <Button onClick={startCamera}>
              <Camera /> Start camera
            </Button>
          }
        />
      )}
    </div>
  );
}
