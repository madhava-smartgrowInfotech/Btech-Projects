import { useEffect, useLayoutEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion, useReducedMotion } from "motion/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import "lenis/dist/lenis.css";
import {
  ArrowRight, BellRing, BrainCircuit, Check, Cpu, Headset, MapPinned, Navigation, Radar as RadarIcon, Settings2, ShieldCheck, Smartphone, WifiOff,
} from "lucide-react";
import { Logo } from "@/components/brand/Logo";
import { CoveragePreview } from "@/components/landing/CoveragePreview";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import CountUp from "@/components/reactbits/CountUp";
import Radar from "@/components/reactbits/Radar";
import RotatingText from "@/components/reactbits/RotatingText";
import SpotlightCard from "@/components/reactbits/SpotlightCard";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useTheme } from "@/lib/theme";

gsap.registerPlugin(ScrollTrigger);

interface PublicStats { readings: number; zones: number; complaints_registered: number; classifier_accuracy: number | null; classifier_model: string | null; predictor_gain_vs_idw: number | null }

const STEPS = [
  { icon: Smartphone, title: "Measure", text: "The field probe on any Android phone, or an ESP32 sensor node, measures latency, loss and speed every few seconds with GPS. Readings wait on the device while it is offline." },
  { icon: BrainCircuit, title: "Classify", text: "Every reading becomes Strong, Weak or Dead with a confidence score - service-quality rules for phones, a trained neural network for radio metrics." },
  { icon: MapPinned, title: "Map", text: "Readings roll up into hexagons of about 0.1 km² per operator and appear on the live map within seconds, as a heat map or hexagons." },
  { icon: BellRing, title: "Act", text: "A zone that stays weak or dead becomes a complaint with its evidence attached. The operator desk is notified by email or Telegram, and people nearby are pointed to better signal." },
  { icon: ShieldCheck, title: "Verify", text: "When the desk marks a fix, new readings from the zone confirm it automatically - or reopen the complaint if service is still poor." },
];

const FEATURES = [
  { icon: RadarIcon, title: "Measured, not guessed", text: "Round-trip time, loss and download speed from real devices, labelled with a confidence you can see." },
  { icon: MapPinned, title: "Coverage you can see", text: "Heat and hexagon maps by operator, period and time of day show exactly where service fails - live." },
  { icon: Navigation, title: "Better signal, nearby", text: "A Gaussian Process predicts service around you and points to the closest strong spot, with its uncertainty." },
  { icon: BellRing, title: "Complaints that file themselves", text: "Persistent weak or dead zones are registered with the readings behind them - no forms, no guesswork." },
  { icon: WifiOff, title: "Works offline", text: "The probe keeps measuring without a connection and syncs every queued reading the moment it returns." },
  { icon: Cpu, title: "Phones and sensor nodes", text: "Add fixed ESP32 nodes to watch community Wi-Fi around the clock alongside people's phones." },
];

const ROLES = [
  { icon: Smartphone, title: "Field users", points: ["Measure with a phone - no app install", "See the coverage map and better spots nearby", "Report a problem in two taps", "Follow each complaint to its fix"] },
  { icon: Headset, title: "Network engineers", points: ["A queue of complaints with evidence", "Assign, acknowledge, resolve", "Automatic verification from new readings", "Analytics by area, operator and hour"] },
  { icon: Settings2, title: "Administrators", points: ["Users and roles", "Detection and verification thresholds", "Email and Telegram notifications", "Model performance and field validation"] },
];

function useSmoothScroll(enabled: boolean) {
  useEffect(() => {
    if (!enabled) return;
    const lenis = new Lenis({ duration: 1.1, smoothWheel: true, anchors: { offset: -72 } });
    lenis.on("scroll", ScrollTrigger.update);
    const tick = (time: number) => lenis.raf(time * 1000);
    gsap.ticker.add(tick);
    gsap.ticker.lagSmoothing(0);
    return () => {
      gsap.ticker.remove(tick);
      lenis.destroy();
    };
  }, [enabled]);
}

function SectionTitle({ eyebrow, title, text }: { eyebrow: string; title: string; text: string }) {
  return (
    <div className="mx-auto mb-12 max-w-2xl text-center" data-reveal>
      <p className="text-sm font-semibold uppercase tracking-wider text-primary">{eyebrow}</p>
      <h2 className="mt-2 text-balance text-3xl font-bold sm:text-4xl">{title}</h2>
      <p className="mt-3 text-balance text-muted-foreground">{text}</p>
    </div>
  );
}

export default function Landing() {
  const { user } = useAuth();
  const { resolved } = useTheme();
  const reduce = useReducedMotion() ?? false;
  const root = useRef<HTMLDivElement>(null);
  const stats = useQuery({ queryKey: ["public-stats"], queryFn: async () => (await api.get<PublicStats>("/api/public/stats")).data, staleTime: 60_000 });
  useSmoothScroll(!reduce);

  useLayoutEffect(() => {
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      gsap.utils.toArray<HTMLElement>("[data-reveal]").forEach((el) => {
        gsap.from(el, { opacity: 0, y: 32, duration: 0.8, ease: "power3.out", scrollTrigger: { trigger: el, start: "top 88%", once: true } });
      });
      gsap.utils.toArray<HTMLElement>("[data-step]").forEach((el) => {
        gsap.from(el, { opacity: 0, x: -24, duration: 0.7, ease: "power3.out", scrollTrigger: { trigger: el, start: "top 82%", once: true } });
      });
      gsap.fromTo("[data-progress]", { scaleY: 0 }, { scaleY: 1, ease: "none", scrollTrigger: { trigger: "[data-steps]", start: "top 70%", end: "bottom 65%", scrub: 0.4 } });
      gsap.set("[data-card]", { opacity: 0, y: 36 });
      ScrollTrigger.batch("[data-card]", { start: "top 90%", once: true, onEnter: (els) => gsap.to(els, { opacity: 1, y: 0, duration: 0.7, stagger: 0.08, ease: "power3.out" }) });
    }, root);
    return () => mm.revert();
  }, []);

  const s = stats.data;
  const showStats = !!s && s.readings > 0;

  return (
    <div ref={root} className="min-h-dvh overflow-x-clip">
      <header className="sticky top-0 z-30 border-b bg-background/80 backdrop-blur-md">
        <div className="container flex h-16 items-center justify-between gap-3">
          <Link to="/" aria-label="SignalScout home">
            <Logo compact className="sm:hidden" />
            <Logo className="hidden sm:inline-flex" />
          </Link>
          <nav className="hidden items-center gap-6 text-sm text-muted-foreground md:flex" aria-label="Page sections">
            <a href="#how" className="transition-colors hover:text-foreground">How it works</a>
            <a href="#features" className="transition-colors hover:text-foreground">Features</a>
            <a href="#roles" className="transition-colors hover:text-foreground">Who it is for</a>
          </nav>
          <div className="flex items-center gap-1 sm:gap-2">
            <ThemeToggle />
            {user ? (
              <Button asChild size="sm"><Link to="/app">Open dashboard</Link></Button>
            ) : (
              <>
                <Button asChild variant="ghost" size="sm"><Link to="/login">Sign in</Link></Button>
                <Button asChild size="sm"><Link to="/register">Get started</Link></Button>
              </>
            )}
          </div>
        </div>
      </header>

      <section className="relative isolate overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10 opacity-35 lg:opacity-80 [mask-image:radial-gradient(ellipse_75%_70%_at_72%_45%,black_20%,transparent_75%)]" aria-hidden>
          <Radar key={resolved} color={resolved === "dark" ? "#6f86ff" : "#3d5afe"} backgroundColor={resolved === "dark" ? "#0d0f16" : "#f5f6f9"} lightMode={resolved === "light"}
            scale={0.62} ringCount={7} spokeCount={12} speed={0.45} sweepSpeed={0.9} brightness={resolved === "dark" ? 0.9 : 0.75} falloff={1.6} enableMouseInteraction={false} paused={reduce} />
        </div>
        <div className="container grid items-center gap-12 py-14 sm:py-20 lg:grid-cols-[1.05fr_1fr] lg:py-24">
          <div className="text-center lg:text-left">
            <motion.p initial={reduce ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
              className="mb-5 inline-flex items-center gap-2 rounded-full border bg-card/80 px-3 py-1 text-xs font-medium text-muted-foreground backdrop-blur">
              <span className="h-2 w-2 rounded-full bg-zone-strong" aria-hidden /> Live coverage intelligence for mobile networks
            </motion.p>
            <motion.h1 initial={reduce ? false : { opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
              className="text-balance text-4xl font-bold leading-[1.1] sm:text-5xl xl:text-6xl">
              <span className="flex flex-wrap items-center justify-center gap-x-3 gap-y-2 lg:justify-start">
                Map the
                <RotatingText texts={["dead zones", "weak signal", "slow data", "call drops"]} auto={!reduce} rotationInterval={2600}
                  mainClassName="overflow-hidden rounded-xl bg-primary px-3 py-0.5 text-primary-foreground sm:py-1" splitLevelClassName="overflow-hidden pb-1"
                  staggerFrom="last" staggerDuration={0.025} initial={{ y: "100%" }} animate={{ y: 0 }} exit={{ y: "-120%" }}
                  transition={{ type: "spring", damping: 30, stiffness: 400 }} />
              </span>
              <span className="mt-2 block">and get them fixed.</span>
            </motion.h1>
            <motion.p initial={reduce ? false : { opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 }}
              className="mx-auto mt-6 max-w-xl text-balance text-base text-muted-foreground sm:text-lg lg:mx-0">
              SignalScout turns phone and sensor readings into a live coverage map, points people to better signal nearby and files complaints with the evidence operators need to act.
            </motion.p>
            <motion.div initial={reduce ? false : { opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.18 }}
              className="mt-8 flex flex-col justify-center gap-3 sm:flex-row lg:justify-start">
              <motion.div whileHover={reduce ? undefined : { y: -2 }} whileTap={{ scale: 0.98 }}>
                <Button asChild size="lg" className="w-full sm:w-auto"><Link to={user ? "/app" : "/register"}>Get started <ArrowRight /></Link></Button>
              </motion.div>
              <motion.div whileHover={reduce ? undefined : { y: -2 }} whileTap={{ scale: 0.98 }}>
                <Button asChild size="lg" variant="outline" className="w-full bg-card/70 backdrop-blur sm:w-auto"><Link to="/login">Try a demo account</Link></Button>
              </motion.div>
            </motion.div>
            <ul className="mt-8 flex flex-col items-center gap-x-6 gap-y-2 text-sm text-muted-foreground sm:flex-row sm:flex-wrap sm:justify-center lg:justify-start">
              {["Any Android phone, no install", "Keeps working offline", "Fixes verified by new data"].map((t) => (
                <li key={t} className="flex items-center gap-2"><Check className="h-4 w-4 shrink-0 text-zone-strong" aria-hidden /> {t}</li>
              ))}
            </ul>
          </div>
          <motion.div initial={reduce ? false : { opacity: 0, y: 24, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ delay: 0.2, duration: 0.6 }}
            className="mx-auto w-full max-w-lg">
            <CoveragePreview />
          </motion.div>
        </div>
      </section>

      {showStats && (
        <section className="border-y bg-card/60" aria-label="Numbers from this installation">
          <div className="container grid grid-cols-2 gap-6 py-10 text-center lg:grid-cols-4">
            {[
              { value: s.readings, label: "readings classified", separator: "," },
              { value: s.zones, label: "zones monitored", separator: "," },
              { value: s.complaints_registered, label: "complaints registered", separator: "," },
              ...(s.classifier_accuracy ? [{ value: Math.round(s.classifier_accuracy * 1000) / 10, label: `test accuracy of the zone classifier`, suffix: "%" }] : []),
            ].map((item) => (
              <div key={item.label} data-reveal>
                <p className="font-display text-3xl font-bold tabular sm:text-4xl">
                  {reduce ? item.value.toLocaleString() : <CountUp to={item.value} duration={1.6} separator={"separator" in item ? item.separator : ""} />}
                  {"suffix" in item && item.suffix}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">{item.label}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      <section id="how" className="container scroll-mt-20 py-20 sm:py-28">
        <SectionTitle eyebrow="How it works" title="From one reading to a verified fix" text="The same pipeline runs for every phone and sensor node - no manual steps between a bad reading and an operator's queue." />
        <ol className="relative mx-auto max-w-3xl" data-steps>
          <span className="absolute bottom-6 left-[1.4rem] top-6 w-0.5 rounded-full bg-border" aria-hidden />
          <span data-progress className="absolute bottom-6 left-[1.4rem] top-6 w-0.5 origin-top rounded-full bg-primary" aria-hidden />
          {STEPS.map((st, i) => (
            <li key={st.title} data-step className="relative flex gap-5 pb-10 last:pb-0">
              <span className="relative z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-2 border-primary/30 bg-background text-primary shadow-sm">
                <st.icon className="h-5 w-5" aria-hidden />
              </span>
              <div className="pt-1.5">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Step {i + 1}</p>
                <h3 className="mt-0.5 text-xl font-semibold">{st.title}</h3>
                <p className="mt-1.5 text-muted-foreground">{st.text}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section id="features" className="scroll-mt-20 border-t bg-muted/30 py-20 sm:py-28">
        <div className="container">
          <SectionTitle eyebrow="Features" title="Everything between a bad signal and a fix" text="Built for the people who live with poor coverage and the teams who repair it." />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <motion.div key={f.title} data-card whileHover={reduce ? undefined : { y: -4 }} transition={{ type: "spring", stiffness: 300, damping: 22 }}>
                <SpotlightCard className="h-full" spotlightColor={resolved === "dark" ? "rgba(111, 134, 255, 0.22)" : "rgba(61, 90, 254, 0.12)"}>
                  <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary"><f.icon className="h-5 w-5" aria-hidden /></span>
                  <h3 className="mt-4 text-lg font-semibold">{f.title}</h3>
                  <p className="mt-1.5 text-sm text-muted-foreground">{f.text}</p>
                </SpotlightCard>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section id="roles" className="container scroll-mt-20 py-20 sm:py-28">
        <SectionTitle eyebrow="Who it is for" title="One product, three desks" text="Each role sees what it needs - and every action leaves a trail on the complaint." />
        <div className="grid gap-4 lg:grid-cols-3">
          {ROLES.map((r) => (
            <motion.div key={r.title} data-card whileHover={reduce ? undefined : { y: -4 }} className="rounded-xl border bg-card p-6 shadow-sm">
              <r.icon className="h-6 w-6 text-primary" aria-hidden />
              <h3 className="mt-4 text-lg font-semibold">{r.title}</h3>
              <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                {r.points.map((p) => <li key={p} className="flex gap-2"><Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden />{p}</li>)}
              </ul>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="container pb-20 sm:pb-28">
        <div data-reveal className="relative overflow-hidden rounded-2xl bg-primary px-6 py-12 text-center text-primary-foreground sm:px-12">
          <div className="absolute inset-0 bg-grid opacity-20 [mask-image:radial-gradient(ellipse_at_center,black_20%,transparent_75%)]" aria-hidden />
          <h2 className="relative text-balance text-3xl font-bold sm:text-4xl">See your coverage in minutes</h2>
          <p className="relative mx-auto mt-3 max-w-xl text-balance opacity-90">Sign in with a demo account to explore sample data, or create an account and connect your phone with a QR code.</p>
          <div className="relative mt-7 flex flex-col justify-center gap-3 sm:flex-row">
            <motion.div whileHover={reduce ? undefined : { y: -2 }} whileTap={{ scale: 0.98 }}>
              <Button asChild size="lg" variant="secondary" className="w-full sm:w-auto"><Link to={user ? "/app" : "/register"}>Create an account <ArrowRight /></Link></Button>
            </motion.div>
            <motion.div whileHover={reduce ? undefined : { y: -2 }} whileTap={{ scale: 0.98 }}>
              <Button asChild size="lg" variant="ghost" className="w-full border border-primary-foreground/30 text-primary-foreground hover:bg-primary-foreground/10 hover:text-primary-foreground sm:w-auto"><Link to="/login">Sign in</Link></Button>
            </motion.div>
          </div>
        </div>
      </section>

      <footer className="border-t">
        <div className="container grid gap-8 py-10 sm:grid-cols-[1.5fr_1fr_1fr]">
          <div>
            <Logo />
            <p className="mt-3 max-w-xs text-sm text-muted-foreground">Coverage data you can act on - from the first weak reading to a verified fix.</p>
          </div>
          <nav aria-label="Product">
            <p className="text-sm font-semibold">Product</p>
            <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
              <li><Link to="/app/map" className="hover:text-foreground">Coverage map</Link></li>
              <li><Link to="/probe" className="hover:text-foreground">Field probe</Link></li>
              <li><Link to="/app/analytics" className="hover:text-foreground">Analytics</Link></li>
            </ul>
          </nav>
          <nav aria-label="Account">
            <p className="text-sm font-semibold">Account</p>
            <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
              <li><Link to="/login" className="hover:text-foreground">Sign in</Link></li>
              <li><Link to="/register" className="hover:text-foreground">Create an account</Link></li>
            </ul>
          </nav>
        </div>
        <div className="border-t">
          <p className="container py-5 text-xs text-muted-foreground">© {new Date().getFullYear()} SignalScout. Map tiles © OpenStreetMap contributors.</p>
        </div>
      </footer>
    </div>
  );
}
