import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Copy, MapPin, Send } from "lucide-react";
import { lazy, Suspense, useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router";

import { SlideUp } from "@/components/motion/SlideUp";
import type { Point } from "@/components/map/LocationPicker";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Textarea, Label } from "@/components/ui/Field";
import { Skeleton } from "@/components/ui/Feedback";
import { FileDrop } from "@/components/ui/FileDrop";
import { PageHeader } from "@/components/ui/Layout";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage } from "@/lib/api";
import { keys } from "@/lib/queries";
import type { CitizenComplaint } from "@/lib/types";

const LocationPicker = lazy(() => import("@/components/map/LocationPicker"));

const EXAMPLES = [
  { label: "हिंदी: पानी की सप्लाई", text: "हमारे मोहल्ले में पिछले 5 दिन से पानी की सप्लाई बंद है, बच्चे और बुजुर्ग बहुत परेशान हैं।" },
  { label: "Hinglish: gaddha", text: "Main road par bahut bada gaddha hai, kal raat ek bike wala gir gaya. Jaldi theek karwaiye." },
  { label: "English: garbage", text: "Garbage has not been collected from our lane for a week and it is starting to smell." },
];
const PHOTO_TYPES = ["image/jpeg", "image/png", "image/webp"];

function PhotoPreview({ file }: { file: File }) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    const u = URL.createObjectURL(file);
    setUrl(u);
    return () => URL.revokeObjectURL(u);
  }, [file]);
  return url ? <img src={url} alt="The photo you selected" className="h-40 w-full rounded-xl border border-[var(--glass-border)] object-cover sm:w-auto" /> : null;
}

export default function FileComplaint() {
  const qc = useQueryClient();
  const [text, setText] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [point, setPoint] = useState<Point | null>(null);
  const [formError, setFormError] = useState("");
  const [done, setDone] = useState<CitizenComplaint | null>(null);

  const submit = useMutation({
    mutationFn: async () => {
      const fd = new FormData();
      fd.append("text", text);
      if (point) {
        fd.append("lat", String(point.lat));
        fd.append("lng", String(point.lng));
      }
      if (photo) fd.append("photo", photo);
      return (await api.post<CitizenComplaint>("/complaints", fd)).data;
    },
    onSuccess: (data) => {
      setDone(data);
      qc.invalidateQueries({ queryKey: keys.mine });
      toast.success(`Complaint registered: ${data.tracking_id}`);
    },
    onError: (err) => setFormError(errorMessage(err)),
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (text.trim().length < 15) return setFormError("Please describe the problem in a little more detail (at least 15 characters).");
    setFormError("");
    submit.mutate();
  }

  function reset() {
    setDone(null);
    setText("");
    setPhoto(null);
    setPoint(null);
    setFormError("");
  }

  if (done)
    return (
      <SlideUp className="mx-auto max-w-lg">
        <Card strong className="space-y-5 p-8 text-center">
          <span className="mx-auto grid size-16 place-items-center rounded-2xl bg-success/15 text-success">
            <CheckCircle2 className="size-9" />
          </span>
          <div className="space-y-1">
            <h1 className="font-display text-2xl font-semibold">Complaint registered</h1>
            <p className="text-sm text-muted-foreground">Keep this tracking ID to follow progress.</p>
          </div>
          <div className="glass-flat flex items-center justify-center gap-3 rounded-2xl py-4">
            <span className="font-mono text-2xl font-semibold tracking-wider" aria-label={`Tracking ID ${done.tracking_id}`}>
              {done.tracking_id}
            </span>
            <Button
              variant="ghost"
              size="icon-sm"
              magnetic={false}
              aria-label="Copy tracking ID"
              onClick={() => navigator.clipboard?.writeText(done.tracking_id).then(() => toast.success("Tracking ID copied"), () => toast.error("Could not copy - select the ID manually"))}
            >
              <Copy />
            </Button>
          </div>
          {done.ward && (
            <p className="flex items-center justify-center gap-1.5 text-sm text-muted-foreground">
              <MapPin className="size-4" /> Ward: {done.ward}
            </p>
          )}
          <p className="text-sm text-muted-foreground">An officer will review it shortly. The department and expected date appear once they confirm.</p>
          <div className="flex flex-wrap justify-center gap-3">
            <Button asChild>
              <Link to={`/app/track/${done.tracking_id}`}>Track status</Link>
            </Button>
            <Button variant="secondary" onClick={reset} magnetic={false}>
              File another
            </Button>
          </div>
        </Card>
      </SlideUp>
    );

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title="File a complaint" description="Write in English, हिंदी or Hinglish. Add a photo and pin the location if you can." />
      <form onSubmit={onSubmit} className="space-y-5">
        <Card>
          <CardHeader title="What is the problem?" description="Say what it is, where, and since when." />
          <CardBody className="space-y-3">
            <Label htmlFor="complaint-text" className="sr-only">
              Complaint description
            </Label>
            <Textarea
              id="complaint-text"
              className="min-h-36"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Describe the issue, where it is and since when…"
              maxLength={4000}
              aria-invalid={formError && text.trim().length < 15 ? true : undefined}
            />
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-muted-foreground">Try an example:</span>
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.label}
                  type="button"
                  onClick={() => setText(ex.text)}
                  className="rounded-full border border-[var(--glass-border)] bg-muted px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-[var(--violet)] hover:text-foreground"
                >
                  {ex.label}
                </button>
              ))}
              <span className="ml-auto text-xs tabular-nums text-muted-foreground">{text.length} / 4000</span>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Photo" description="Optional. JPG, PNG or WebP, up to 8 MB." />
          <CardBody>
            <FileDrop
              file={photo}
              onFile={setPhoto}
              accept="image/jpeg,image/png,image/webp"
              onPick={() => setFormError("")}
              validate={(f) =>
                !PHOTO_TYPES.includes(f.type) ? "Photo must be a JPG, PNG or WebP image." : f.size > 8 * 1024 * 1024 ? "Photo must be smaller than 8 MB." : null
              }
              title="Drop a photo here, or click to browse"
              hint="JPG, PNG or WebP · up to 8 MB"
              disabled={submit.isPending}
            >
              {photo && <PhotoPreview file={photo} />}
            </FileDrop>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Location" description="Tap the map to pin where the problem is." />
          <CardBody>
            <Suspense fallback={<Skeleton className="h-72 w-full rounded-2xl" />}>
              <LocationPicker value={point} onChange={setPoint} />
            </Suspense>
          </CardBody>
        </Card>

        {formError && (
          <p role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.07] px-4 py-3 text-sm text-danger">
            {formError}
          </p>
        )}
        <div className="flex justify-end">
          <Button type="submit" size="lg" loading={submit.isPending}>
            {!submit.isPending && <Send />} {submit.isPending ? "Analysing and submitting…" : "Submit complaint"}
          </Button>
        </div>
      </form>
    </div>
  );
}
