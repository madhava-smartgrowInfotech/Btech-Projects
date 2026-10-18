import { ArrowRight, Camera, Dumbbell, Hand, Volume2 } from "lucide-react";
import { Link } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { PipelinePreview } from "@/components/landing/PipelinePreview";
import { StatsStrip } from "@/components/landing/StatsStrip";
import { FadeIn, Marquee, Reveal, SlideUp, SmoothScroll } from "@/components/motion";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ThemeToggle } from "@/components/ui/AppShell";
import { useAbout } from "@/lib/queries";

const LETTERS = Array.from({ length: 26 }, (_, i) => String.fromCharCode(65 + i));

const FEATURES = [
  { icon: Camera, title: "Collect", text: "Capture your own hand images per letter, one at a time or in bursts, with a live silhouette preview.", to: "/app/collect" },
  { icon: Dumbbell, title: "Train", text: "Tune epochs, batch size and learning rate, then watch accuracy and loss climb epoch by epoch.", to: "/app/train" },
  { icon: Hand, title: "Recognize", text: "Spell with your hands. Steady signs are typed into a sentence, with space and delete gestures.", to: "/app/recognize" },
  { icon: Volume2, title: "Speak", text: "Read the finished sentence aloud with offline text-to-speech.", to: "/app/recognize" },
];

export default function Landing() {
  const about = useAbout();
  return (
    <div className="min-h-dvh">
      <SmoothScroll />
      <AuroraBackground />
      <a href="#top" className="sr-only z-[90] rounded-lg bg-popover px-3 py-2 focus:not-sr-only focus:fixed focus:left-3 focus:top-3">
        Skip to content
      </a>

      <header className="sticky top-0 z-40 px-3 pt-3">
        <div className="glass mx-auto flex h-14 max-w-6xl items-center gap-2 rounded-2xl px-3 sm:px-4">
          <Link to="/" aria-label="SignSpeak home">
            <Logo />
          </Link>
          <nav aria-label="Page sections" className="ml-6 hidden items-center gap-1 md:flex">
            <a href="#how-it-works" className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground">
              How it works
            </a>
            <a href="#features" className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground">
              Features
            </a>
          </nav>
          <div className="ml-auto flex items-center gap-1">
            <ThemeToggle />
            <Button asChild size="sm">
              <Link to="/app">Open app</Link>
            </Button>
          </div>
        </div>
      </header>

      <main id="top">
        <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-16 pt-14 sm:px-6 lg:grid-cols-[1.1fr_1fr] lg:pb-24 lg:pt-20">
          <div className="space-y-6">
            <FadeIn>
              <Badge tone="violet" className="px-3 py-1 text-xs">
                ASL alphabet · CNN · live webcam
              </Badge>
            </FadeIn>
            <SlideUp delay={0.05}>
              <h1 className="font-display text-4xl font-bold leading-[1.05] tracking-tight text-balance sm:text-5xl lg:text-6xl">
                Sign it. See it. <span className="text-gradient">Hear it.</span>
              </h1>
            </SlideUp>
            <SlideUp delay={0.12}>
              <p className="max-w-xl text-lg text-muted-foreground">
                SignSpeak reads American Sign Language letters from your webcam with a convolutional neural network, types them into a sentence and speaks it aloud. Train it on your own hands.
              </p>
            </SlideUp>
            <SlideUp delay={0.2} className="flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link to="/app/recognize">
                  Start recognizing <ArrowRight />
                </Link>
              </Button>
              <Button asChild size="lg" variant="secondary">
                <Link to="/app/collect">Collect your data</Link>
              </Button>
            </SlideUp>
          </div>
          <PipelinePreview />
        </section>

        <section aria-label="Supported signs" className="pb-16">
          <Marquee speed={60}>
            {LETTERS.map((l) => (
              <span key={l} className="glass grid size-14 place-items-center rounded-2xl font-display text-2xl font-semibold text-gradient">
                {l}
              </span>
            ))}
            {["space", "del", "nothing"].map((l) => (
              <span key={l} className="glass grid h-14 place-items-center rounded-2xl px-5 font-display text-lg font-semibold text-muted-foreground">
                {l}
              </span>
            ))}
          </Marquee>
        </section>

        <StatsStrip />

        <HowItWorks />

        <section id="features" className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <div className="mb-10 space-y-3 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Everything in one place</p>
            <h2 className="font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
              Collect, train, recognize, <span className="text-gradient">speak</span>
            </h2>
          </div>
          <Reveal className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map(({ icon: Icon, title, text, to }) => (
              <Link key={title} to={to} data-reveal className="glass sweep group flex flex-col gap-3 rounded-3xl p-5 transition-transform duration-300 hover:-translate-y-1">
                <span className="grid size-11 place-items-center rounded-2xl bg-grad-primary text-white shadow-[0_10px_24px_-10px_rgba(124,92,255,0.9)]">
                  <Icon className="size-5" />
                </span>
                <h3 className="font-display text-lg font-semibold">{title}</h3>
                <p className="text-sm text-muted-foreground">{text}</p>
                <span className="mt-auto inline-flex items-center gap-1 text-sm font-medium text-violet-ink">
                  Open <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
                </span>
              </Link>
            ))}
          </Reveal>
        </section>
      </main>

      <footer className="mx-auto max-w-6xl px-4 pb-10 sm:px-6">
        <div className="glass flex flex-col gap-3 rounded-3xl p-5 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <Logo />
          <p className="max-w-xl sm:text-right">
            {about.data ? (
              <>
                Builds on <span className="text-foreground">{about.data.base_paper["Title"]}</span>, {about.data.base_paper["Published In"]} {about.data.base_paper["Year"]}.
              </>
            ) : (
              "CSE-A · Batch 16 · Sign Language Recognition System based on CNNs"
            )}
          </p>
        </div>
      </footer>
    </div>
  );
}
