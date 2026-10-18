import { Camera, CameraOff, Loader2, TriangleAlert } from "lucide-react";
import type { ReactNode, RefObject } from "react";

import { Button } from "@/components/ui/Button";
import { FRAME_H, FRAME_W, type CameraState } from "@/lib/camera";
import type { AppConfig } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Mirrored webcam preview with the cyan region-of-interest box over it. The box uses the API's own
 * ROI numbers (sign_language_app.preprocessing.get_roi_box on a 960x540 frame), so what you see
 * inside it is exactly what the server crops.
 */
export function CameraView({
  videoRef,
  state,
  error,
  roi,
  onStart,
  children,
  className,
}: {
  videoRef: RefObject<HTMLVideoElement>;
  state: CameraState;
  error: string | null;
  roi?: AppConfig["roi"];
  onStart: () => void;
  children?: ReactNode;
  className?: string;
}) {
  const running = state === "running";
  const box = roi ?? { x1: 620, y1: 90, x2: 920, y2: 390 };
  return (
    <div
      className={cn("relative aspect-video w-full overflow-hidden rounded-2xl border border-[var(--glass-border)] bg-black/80", className)}
      style={{ aspectRatio: `${FRAME_W} / ${FRAME_H}` }}
    >
      <video
        ref={videoRef}
        muted
        playsInline
        aria-label="Live webcam preview"
        className={cn("absolute inset-0 size-full -scale-x-100 object-cover", !running && "invisible")}
      />
      {running && (
        <div
          aria-hidden
          className="absolute rounded-md border-2 border-cyan shadow-[0_0_0_9999px_rgba(2,6,23,0.35),0_0_24px_rgba(34,211,238,0.55)]"
          style={{
            left: `${(box.x1 / FRAME_W) * 100}%`,
            top: `${(box.y1 / FRAME_H) * 100}%`,
            width: `${((box.x2 - box.x1) / FRAME_W) * 100}%`,
            height: `${((box.y2 - box.y1) / FRAME_H) * 100}%`,
          }}
        >
          <span className="absolute -top-6 left-0 rounded-md bg-cyan px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-900">
            Hand here
          </span>
        </div>
      )}
      {running && children}
      {!running && (
        <div className="absolute inset-0 grid place-items-center p-4 text-center">
          {state === "starting" ? (
            <div role="status" className="flex flex-col items-center gap-2 text-sm text-slate-200">
              <Loader2 className="size-6 animate-spin text-cyan" /> Opening the webcam…
            </div>
          ) : state === "error" ? (
            <div role="alert" className="flex max-w-sm flex-col items-center gap-3">
              <span className="grid size-12 place-items-center rounded-2xl bg-danger/20 text-danger">
                <TriangleAlert className="size-6" />
              </span>
              <p className="text-sm text-slate-100">{error}</p>
              <Button size="sm" variant="secondary" onClick={onStart}>
                <Camera /> Try again
              </Button>
            </div>
          ) : (
            <div className="flex max-w-xs flex-col items-center gap-3 text-slate-200">
              <span className="grid size-12 place-items-center rounded-2xl bg-white/10">
                <CameraOff className="size-6" />
              </span>
              <p className="text-sm">The camera is off. Your browser will ask for permission the first time.</p>
              <Button onClick={onStart}>
                <Camera /> Start camera
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
