import { Camera, CameraOff, Cpu, Eye } from "lucide-react";
import type { RefObject } from "react";

import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import type { SessionState } from "@/lib/types";
import { verdictTone } from "@/lib/verdict";

/**
 * Left-hand preview. Camera: the server's landmark-annotated frame (mirrored like a selfie view); until the first
 * annotated frame arrives the raw camera feed fills in. Simulation: a scenario panel (there is no video to show).
 * Nothing here is ever saved: frames live in RAM on the server and are dropped after processing.
 */
/** Solid-ish glass so badge text stays readable over any camera image. */
const OVERLAY = "bg-[color-mix(in_srgb,var(--background)_78%,transparent)] backdrop-blur-md";

export function PreviewPanel({
  state,
  preview,
  videoRef,
  cameraRunning,
}: {
  state: SessionState | null;
  preview: string | null;
  videoRef: RefObject<HTMLVideoElement>;
  cameraRunning: boolean;
}) {
  const source = state?.source ?? "none";
  const showImage = source === "camera" && preview;
  const showLive = source === "camera" && !preview && cameraRunning;
  return (
    <div className="glass-strong relative aspect-[4/3] w-full overflow-hidden rounded-2xl">
      {/* The video element must stay mounted for the hook; it is visible only until the first annotated frame. */}
      <video
        ref={videoRef}
        muted
        playsInline
        aria-label="Raw camera feed"
        className={cn("absolute inset-0 size-full -scale-x-100 object-cover", showLive ? "opacity-100" : "pointer-events-none opacity-0")}
      />
      {showImage && (
        <img src={preview} alt="Camera frame with eye landmarks drawn on it" className="absolute inset-0 size-full -scale-x-100 object-cover" />
      )}

      {source === "none" && (
        <div className="absolute inset-0 grid place-items-center p-6 text-center">
          <div className="space-y-3">
            <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-grad-soft text-violet-ink ring-1 ring-[var(--glass-border)]">
              <CameraOff className="size-6" />
            </span>
            <p className="font-display text-lg font-semibold">Camera stopped</p>
            <p className="mx-auto max-w-xs text-sm text-muted-foreground">
              No video or face images are saved. Start the camera, or pick Simulation to try the rules without one.
            </p>
          </div>
        </div>
      )}

      {source === "simulation" && state && (
        <div className="absolute inset-0 grid place-items-center p-6 text-center">
          <div className="space-y-3">
            <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-grad-primary text-white shadow-[0_10px_30px_-10px_rgba(124,92,255,0.8)]">
              <Cpu className="size-6" />
            </span>
            <Badge tone="magenta">SIMULATION</Badge>
            <p className="font-display text-xl font-semibold">{state.scenario}</p>
            <p className="mx-auto max-w-xs text-sm text-muted-foreground">Scripted measurements; not a camera prediction.</p>
          </div>
        </div>
      )}

      {source === "camera" && !showImage && !showLive && (
        <div className="absolute inset-0 grid place-items-center p-6 text-center text-sm text-muted-foreground">
          <div className="space-y-2">
            <Camera className="mx-auto size-6 animate-pulse text-violet-ink" />
            <p>Opening webcam and landmark model…</p>
          </div>
        </div>
      )}

      {/* overlays */}
      {state && source !== "none" && (
        <>
          <div className="absolute left-3 top-3 flex flex-wrap items-center gap-2">
            <Badge tone={source === "simulation" ? "magenta" : "cyan"} className={OVERLAY}>
              {source === "simulation" ? "SIMULATION" : "LIVE CAMERA"}
            </Badge>
            {state.monitoring && <Badge tone="violet" className={OVERLAY}>Monitoring</Badge>}
          </div>
          <div className="absolute inset-x-3 bottom-3 flex flex-wrap items-center justify-between gap-2">
            <Badge tone={verdictTone(state.state)} className={cn(OVERLAY, "px-2.5 py-1 text-xs")}>
              <Eye /> {state.state}
            </Badge>
            <Badge tone={state.quality === "Good" ? "success" : "warning"} className={OVERLAY}>
              Signal: {state.quality}
            </Badge>
          </div>
        </>
      )}
    </div>
  );
}
