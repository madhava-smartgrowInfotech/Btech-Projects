import { ClipboardCheck, MessageSquareText, Sparkles, Upload } from "lucide-react";
import { useEffect, useLayoutEffect, useRef, useState } from "react";

import { Reveal } from "@/components/motion/Reveal";
import { gsap, ScrollTrigger } from "@/lib/gsap";
import { cn } from "@/lib/utils";

const STEPS = [
  {
    icon: Upload,
    title: "Upload your study material",
    text: "Drop in a PDF, DOCX or TXT - syllabi, notes, question banks. The text is extracted, split into searchable chunks and its main topics are detected.",
  },
  {
    icon: MessageSquareText,
    title: "Ask in plain words",
    text: "Answers are built from the passages of your own documents that match your question best, and the source file is shown next to every answer.",
  },
  {
    icon: ClipboardCheck,
    title: "Take an auto-made quiz",
    text: "Pick a document and get five fill-in-the-blank multiple-choice questions generated from its key terms. Submit to see what you got right.",
  },
  {
    icon: Sparkles,
    title: "Follow your roadmap",
    text: "Every answer feeds a per-topic accuracy score. Topics below 50% become High priority, 50-80% Medium and above that Low.",
  },
];

function Heading() {
  return (
    <div className="space-y-3">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">How it works</p>
      <h2 className="font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
        From a stack of notes to a <span className="text-gradient">study plan</span>
      </h2>
      <p className="max-w-md text-muted-foreground">Four steps from your first upload to a priority-ranked list of what to revise.</p>
    </div>
  );
}

/**
 * Desktop (and motion allowed): the section pins while the four steps play through, scrubbed by
 * scroll (GSAP ScrollTrigger). Phones / reduced motion: a plain list revealed on scroll.
 */
export function HowItWorks() {
  const root = useRef<HTMLElement>(null);
  const [active, setActive] = useState(0);
  const [pinned, setPinned] = useState(false);

  useLayoutEffect(() => {
    const el = root.current;
    if (!el) return;
    const mm = gsap.matchMedia();
    mm.add("(min-width: 1024px) and (prefers-reduced-motion: no-preference)", () => {
      setPinned(true);
      const cards = gsap.utils.toArray<HTMLElement>(".hiw-card", el);
      gsap.set(cards, { autoAlpha: 0, y: 60, scale: 0.94 });
      gsap.set(cards[0], { autoAlpha: 1, y: 0, scale: 1 });
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: el,
          start: "top top",
          end: `+=${STEPS.length * 70}%`,
          pin: true,
          scrub: 0.6,
          onUpdate: (self) => setActive(Math.min(STEPS.length - 1, Math.floor(self.progress * STEPS.length * 0.999))),
        },
      });
      tl.fromTo(".hiw-progress", { scaleY: 0 }, { scaleY: 1, ease: "none", duration: STEPS.length - 1 }, 0);
      cards.forEach((card, i) => {
        if (i === 0) return;
        tl.to(cards[i - 1], { autoAlpha: 0, y: -60, scale: 0.94, duration: 0.5 }, i - 0.6);
        tl.to(card, { autoAlpha: 1, y: 0, scale: 1, duration: 0.5 }, i - 0.5);
      });
      return () => setPinned(false);
    });
    return () => mm.revert();
  }, []);

  // the layout switch changes page height - re-measure every trigger
  useEffect(() => {
    const id = requestAnimationFrame(() => ScrollTrigger.refresh());
    return () => cancelAnimationFrame(id);
  }, [pinned]);

  return (
    <section ref={root} id="how-it-works" className="relative">
      {/* Pinned desktop layout */}
      <div className={cn("mx-auto hidden min-h-dvh max-w-6xl items-center gap-16 px-6 py-24", pinned && "lg:grid lg:grid-cols-[1fr_1.1fr]")}>
        <div className="space-y-10">
          <Heading />
          <ol className="relative space-y-1">
            <span aria-hidden className="absolute bottom-4 left-[19px] top-4 w-px bg-[var(--glass-border)]" />
            <span aria-hidden className="hiw-progress absolute bottom-4 left-[19px] top-4 w-px origin-top bg-grad-primary" />
            {STEPS.map((s, i) => (
              <li key={s.title} className="relative flex items-center gap-4 py-2">
                <span
                  className={cn(
                    "relative grid size-10 shrink-0 place-items-center rounded-full text-sm font-semibold transition-all duration-500",
                    i <= active
                      ? "bg-grad-primary text-white shadow-[0_0_20px_-4px_rgba(124,92,255,0.8)]"
                      : "bg-[var(--glass-strong)] text-muted-foreground ring-1 ring-[var(--glass-border)]",
                  )}
                >
                  {i + 1}
                </span>
                <span className={cn("font-medium transition-colors duration-500", i === active ? "text-foreground" : "text-muted-foreground")}>
                  {s.title}
                </span>
              </li>
            ))}
          </ol>
        </div>
        <div className="relative h-[380px]">
          <div aria-hidden className="absolute inset-10 rounded-full bg-grad-primary opacity-20 blur-3xl" />
          {STEPS.map(({ icon: Icon, title, text }, i) => (
            <article key={title} className="hiw-card glass-strong absolute inset-0 flex flex-col justify-center gap-5 rounded-3xl p-10">
              <span className="grid size-14 place-items-center rounded-2xl bg-grad-primary text-white shadow-[0_12px_30px_-10px_rgba(124,92,255,0.9)]">
                <Icon className="size-7" />
              </span>
              <p className="text-sm font-medium text-violet-ink">Step {i + 1} of {STEPS.length}</p>
              <h3 className="font-display text-2xl font-semibold">{title}</h3>
              <p className="text-lg leading-relaxed text-muted-foreground">{text}</p>
            </article>
          ))}
        </div>
      </div>

      {/* Phone / tablet / reduced-motion layout */}
      {!pinned && (
        <div className="mx-auto max-w-3xl px-4 py-24 sm:px-6">
          <div className="mb-12 text-center [&_p.max-w-md]:mx-auto">
            <Heading />
          </div>
          <Reveal className="relative space-y-5">
            <span aria-hidden className="absolute bottom-6 left-[19px] top-6 w-px bg-gradient-to-b from-[var(--violet)] via-[var(--magenta)] to-[var(--cyan)] opacity-50" />
            {STEPS.map(({ icon: Icon, title, text }, i) => (
              <div key={title} data-reveal className="relative flex gap-4">
                <span className="relative z-10 grid size-10 shrink-0 place-items-center rounded-full bg-grad-primary text-sm font-semibold text-white ring-4 ring-[var(--background)]">
                  {i + 1}
                </span>
                <div className="glass sweep flex-1 rounded-2xl p-5">
                  <div className="mb-2 flex items-center gap-2">
                    <Icon className="size-5 text-violet-ink" />
                    <h3 className="font-display text-lg font-semibold">{title}</h3>
                  </div>
                  <p className="text-muted-foreground">{text}</p>
                </div>
              </div>
            ))}
          </Reveal>
        </div>
      )}
    </section>
  );
}
