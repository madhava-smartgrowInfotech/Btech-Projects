import { useCallback, useEffect, useRef, useState } from "react";

/** Same geometry as the desktop app's Camera (config.FRAME_WIDTH x FRAME_HEIGHT, mirrored). */
export const FRAME_W = 960;
export const FRAME_H = 540;

export type CameraState = "idle" | "starting" | "running" | "error";

function cameraError(e: unknown): string {
  const name = (e as { name?: string })?.name;
  if (name === "NotAllowedError" || name === "SecurityError")
    return "Camera permission was denied. Allow camera access in the browser's address bar, then press Start camera again.";
  if (name === "NotFoundError" || name === "OverconstrainedError")
    return "No webcam was found. Connect one (or free it from another app) and press Start camera again.";
  if (name === "NotReadableError") return "The webcam is in use by another app. Close it there, then press Start camera again.";
  if (!navigator.mediaDevices?.getUserMedia) return "This browser can't access the camera on this address. Use Chrome or Edge on http://localhost.";
  return "Could not open the webcam.";
}

/**
 * Browser webcam. `grab()` returns a mirrored 960x540 JPEG (cover-cropped, like the display),
 * so the API's ROI crop lands on exactly the box drawn over the video.
 */
export function useCamera() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [state, setState] = useState<CameraState>("idle");
  const [error, setError] = useState<string | null>(null);

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setState("idle");
  }, []);

  const start = useCallback(async () => {
    if (streamRef.current) return true;
    setState("starting");
    setError(null);
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error("unsupported");
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: FRAME_W }, height: { ideal: FRAME_H }, facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      const video = videoRef.current;
      if (video) {
        video.srcObject = stream;
        await video.play().catch(() => undefined);
      }
      setState("running");
      return true;
    } catch (e) {
      setError(cameraError(e));
      setState("error");
      return false;
    }
  }, []);

  useEffect(() => () => streamRef.current?.getTracks().forEach((t) => t.stop()), []);

  const grab = useCallback((quality = 0.85) => {
    const video = videoRef.current;
    if (!video || video.readyState < 2 || !video.videoWidth) return Promise.resolve<Blob | null>(null);
    const canvas = (canvasRef.current ??= document.createElement("canvas"));
    canvas.width = FRAME_W;
    canvas.height = FRAME_H;
    const ctx = canvas.getContext("2d");
    if (!ctx) return Promise.resolve<Blob | null>(null);
    // cover-crop the native frame to 16:9, then mirror horizontally
    const vw = video.videoWidth;
    const vh = video.videoHeight;
    const target = FRAME_W / FRAME_H;
    let sw = vw;
    let sh = vh;
    if (vw / vh > target) sw = vh * target;
    else sh = vw / target;
    const sx = (vw - sw) / 2;
    const sy = (vh - sh) / 2;
    ctx.save();
    ctx.translate(FRAME_W, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, sx, sy, sw, sh, 0, 0, FRAME_W, FRAME_H);
    ctx.restore();
    return new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", quality));
  }, []);

  return { videoRef, state, error, start, stop, grab, running: state === "running" };
}
