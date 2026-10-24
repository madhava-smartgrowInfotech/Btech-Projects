import { Camera, Gauge, ScanFace, ScrollText, Scale, ShieldCheck } from "lucide-react";

import { Reveal } from "@/components/motion/Reveal";

const STEPS = [
  { icon: Camera, title: "Camera", text: "Your webcam frames are resized to 640x480 and kept only in memory. No video or face image is ever saved." },
  { icon: ScanFace, title: "Face landmarks", text: "MediaPipe Face Landmarker finds six points around each eye plus both outer eye corners." },
  { icon: Gauge, title: "Quality gates", text: "Lighting, blur, motion, face count and eye geometry are checked first. A bad frame gives Unable to assess, never a guess." },
  { icon: Scale, title: "Eye aspect ratio", text: "EAR and image-plane head roll are measured and smoothed with a 3-sample median, then compared with your personal threshold." },
  { icon: ScrollText, title: "Explainable rules", text: "Long closure, a high closed-eye fraction over 10 s, or tilt with low EAR must persist before a warning appears." },
  { icon: ShieldCheck, title: "Honest output", text: "Normal, Possible impairment or drowsiness, or Unable to assess, with the reason shown and every event logged as numbers." },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
      <div className="mb-10 space-y-3 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">How it works</p>
        <h2 className="font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
          From a webcam frame to a <span className="text-gradient">transparent warning</span>
        </h2>
        <p className="mx-auto max-w-xl text-muted-foreground">The pipeline from the project, running live through your browser camera.</p>
      </div>
      <Reveal className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {STEPS.map(({ icon: Icon, title, text }, i) => (
          <article key={title} data-reveal className="glass sweep flex flex-col gap-3 rounded-3xl p-6">
            <div className="flex items-center justify-between">
              <span className="grid size-11 place-items-center rounded-2xl bg-grad-primary text-white shadow-[0_10px_24px_-10px_rgba(124,92,255,0.9)]">
                <Icon className="size-5" />
              </span>
              <span className="font-display text-sm font-semibold text-muted-foreground">0{i + 1}</span>
            </div>
            <h3 className="font-display text-lg font-semibold">{title}</h3>
            <p className="text-sm text-muted-foreground">{text}</p>
          </article>
        ))}
      </Reveal>
    </section>
  );
}
