import { useCallback, useEffect, useRef, useState } from "react";

/** Same frame size the desktop app processes (vision.py resizes every frame to 640x480). */
export const FRAME_W = 640;
export const FRAME_H = 480;

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
 * Browser webcam. `grab()` returns a 640x480 JPEG (cover-cropped, NOT mirrored: the landmark model
 * and the desktop app both see the raw camera image; only the on-screen preview is mirrored).
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

  const start = useCallback(async (deviceId?: string) => {
    if (streamRef.current) return true;
    setState("starting");
    setError(null);
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error("unsupported");
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: FRAME_W }, height: { ideal: FRAME_H }, ...(deviceId ? { deviceId: { exact: deviceId } } : { facingMode: "user" }) },
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

  const grab = useCallback((quality = 0.8) => {
    const video = videoRef.current;
    if (!video || video.readyState < 2 || !video.videoWidth) return Promise.resolve<Blob | null>(null);
    const canvas = (canvasRef.current ??= document.createElement("canvas"));
    canvas.width = FRAME_W;
    canvas.height = FRAME_H;
    const ctx = canvas.getContext("2d");
    if (!ctx) return Promise.resolve<Blob | null>(null);
    // cover-crop the native frame to 4:3
    const vw = video.videoWidth;
    const vh = video.videoHeight;
    const target = FRAME_W / FRAME_H;
    let sw = vw;
    let sh = vh;
    if (vw / vh > target) sw = vh * target;
    else sh = vw / target;
    ctx.drawImage(video, (vw - sw) / 2, (vh - sh) / 2, sw, sh, 0, 0, FRAME_W, FRAME_H);
    return new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", quality));
  }, []);

  return { videoRef, state, error, start, stop, grab, running: state === "running" };
}
