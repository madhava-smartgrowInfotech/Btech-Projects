import { useEffect, useRef, useState } from "react";
import { Camera } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface DetectedBarcode {
  rawValue: string;
}
interface BarcodeDetectorLike {
  detect(source: CanvasImageSource): Promise<DetectedBarcode[]>;
}
declare global {
  interface Window {
    BarcodeDetector?: new (options: { formats: string[] }) => BarcodeDetectorLike;
  }
}

/** Camera scanning, offered only where the browser can decode QR codes and allows the camera. */
export const cameraScanSupported = () =>
  typeof window !== "undefined" && window.isSecureContext && Boolean(window.BarcodeDetector) && Boolean(navigator.mediaDevices?.getUserMedia);

export function CameraScanner({ onCode, disabled }: { onCode: (code: string) => void; disabled?: boolean }) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const video = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (!open) return;
    let stream: MediaStream | null = null;
    let stopped = false;
    let timer = 0;
    const detector = new window.BarcodeDetector!({ formats: ["qr_code"] });

    (async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
        if (!video.current) return;
        video.current.srcObject = stream;
        await video.current.play();
        const tick = async () => {
          if (stopped || !video.current) return;
          try {
            const codes = await detector.detect(video.current);
            if (codes[0]?.rawValue) {
              onCode(codes[0].rawValue);
              setOpen(false);
              return;
            }
          } catch {
            /* keep trying */
          }
          timer = window.setTimeout(tick, 250);
        };
        void tick();
      } catch {
        setError("The camera could not be opened. Allow camera access or use a handheld scanner.");
      }
    })();

    return () => {
      stopped = true;
      window.clearTimeout(timer);
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, [open, onCode]);

  if (!cameraScanSupported()) return null;
  return (
    <>
      <Button type="button" variant="outline" size="lg" disabled={disabled} onClick={() => { setError(null); setOpen(true); }}>
        <Camera /> Camera
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Scan a seat slip</DialogTitle>
            <DialogDescription>Hold the QR code on the candidate's slip in front of the camera.</DialogDescription>
          </DialogHeader>
          {error ? (
            <p className="text-sm text-destructive">{error}</p>
          ) : (
            <video ref={video} className="aspect-video w-full rounded-lg bg-black object-cover" muted playsInline />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
