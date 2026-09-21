import { useEffect, useLayoutEffect, useRef, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion, useReducedMotion } from "motion/react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import {
  Accessibility, ArrowRight, BarChart3, ClipboardCheck, FileSpreadsheet, Fingerprint, Grid3x3, Hash, LayoutGrid, QrCode,
  Search, ShieldCheck, Shuffle, Sparkles, Upload,
} from "lucide-react";
import { HeroHall, ComparisonGrids } from "@/components/landing/HeroHall";
import { PublicFooter, PublicHeader } from "@/components/layout/PublicShell";
import BlurText from "@/components/reactbits/BlurText";
import CountUp from "@/components/reactbits/CountUp";
import DotGrid from "@/components/reactbits/DotGrid";
import RotatingText from "@/components/reactbits/RotatingText";
import SpotlightCard from "@/components/reactbits/SpotlightCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useTheme } from "@/lib/theme";

gsap.registerPlugin(ScrollTrigger);

interface EngineSummary {
  available: boolean;
  typical_candidates?: number;
  typical_solve_s?: number;
  conflicts_avoided?: number;
  same_paper_pairs?: number;
  roll_seat_correlation?: number;
  neighbour_overlap?: number;
  runs?: number;
  largest_candidates?: number;
  largest_solve_s?: number;
  all_hard_rules_satisfied?: boolean;
}

const STEPS = [
  { icon: Upload, title: "Import", text: "Drop in the Excel or CSV templates for courses, halls, candidates and the timetable. Every row is checked - unknown courses, duplicate IDs, timetable clashes - before anything is saved." },
  { icon: Sparkles, title: "Optimise", text: "OR-Tools CP-SAT shares candidates between halls and colour classes, then lays out every hall in parallel: no same-paper neighbours, roll numbers spread apart, accessible seats honoured." },
  { icon: LayoutGrid, title: "Review and publish", text: "Open any hall, drag a candidate to another seat and see live why a move is or is not allowed. Publish when ready - every seed and every move is in the audit trail." },
  { icon: ClipboardCheck, title: "On the day", text: "Candidates find their seat online and carry a QR slip. Invigilators mark attendance on a tablet and submit the register; reports update as they go." },
];

const FEATURES = [
  { icon: FileSpreadsheet, title: "Validated import", text: "Excel and CSV templates with row-by-row checks, including subject-combination clashes." },
  { icon: Sparkles, title: "Constraint optimisation", text: "CP-SAT respects capacity, paper separation (diagonals too), roll-number gaps, department mix and accessible seats." },
  { icon: Shuffle, title: "Seeded, fair randomness", text: "A random valid plan every time - reproducible from its seed, verified with one click." },
  { icon: Grid3x3, title: "Visual seat maps", text: "Drag to swap with live rule checks. Tap-to-swap on tablets, keyboard friendly." },
  { icon: FileSpreadsheet, title: "Charts and lists", text: "Seating charts and invigilator sheets as PDF, hall-wise and door lists in Excel." },
  { icon: ClipboardCheck, title: "Tablet attendance", text: "Scan a slip or tap a seat. Registers lock on submit; progress is live for the controller." },
  { icon: QrCode, title: "Seat lookup and QR slips", text: "Candidates look up their hall and seat by ID and download a slip with a QR code." },
  { icon: BarChart3, title: "Analytics", text: "Utilisation, rules met, conflicts avoided versus roll order, attendance and solve times." },
];

function useSmoothScroll(enabled: boolean) {
  useEffect(() => {
    if (!enabled) return;
    const lenis = new Lenis({ duration: 1.1, smoothWheel: true });
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

export default function LandingPage() {
  const { user } = useAuth();
  const { resolved } = useTheme();
  const reduce = useReducedMotion();
  const navigate = useNavigate();
  const root = useRef<HTMLDivElement>(null);
  const [candidateId, setCandidateId] = useState("");
  const summary = useQuery({
    queryKey: ["public", "engine-summary"],
    queryFn: async () => (await api.get<EngineSummary>("/public/engine-summary")).data,
    staleTime: Infinity,
  });
  const s = summary.data?.available ? summary.data : null;
  useSmoothScroll(!reduce);

  useLayoutEffect(() => {
    if (reduce || !root.current) return;
    const ctx = gsap.context(() => {
      gsap.utils.toArray<HTMLElement>("[data-reveal]").forEach((el) => {
        gsap.from(el, { y: 36, opacity: 0, duration: 0.8, ease: "power3.out", scrollTrigger: { trigger: el, start: "top 86%" } });
      });
      gsap.fromTo(".hiw-line", { scaleY: 0 }, {
        scaleY: 1, ease: "none", transformOrigin: "top center",
        scrollTrigger: { trigger: ".hiw", start: "top 70%", end: "bottom 60%", scrub: true },
      });
      gsap.utils.toArray<HTMLElement>(".hiw-step").forEach((el) => {
        gsap.from(el, { x: -28, opacity: 0, duration: 0.7, ease: "power2.out", scrollTrigger: { trigger: el, start: "top 80%" } });
      });
      ScrollTrigger.batch(".feature-card", {
        start: "top 90%",
        onEnter: (batch) => gsap.fromTo(batch, { y: 30, opacity: 0 }, { y: 0, opacity: 1, stagger: 0.08, duration: 0.6, ease: "power2.out" }),
      });
    }, root);
    return () => ctx.revert();
  }, [reduce]);

  function findSeat(event: FormEvent) {
    event.preventDefault();
    if (candidateId.trim()) navigate(`/lookup/${encodeURIComponent(candidateId.trim().toUpperCase())}`);
  }

  const dots = resolved === "dark" ? { base: "#1b1e38", active: "#8b84f0" } : { base: "#dfe1f5", active: "#493ee5" };

  return (
    <div ref={root} className="flex min-h-dvh flex-col">
      <PublicHeader transparent />

      {/* Hero */}
      <section className="relative isolate overflow-hidden">
        <div className="absolute inset-0 -z-10" aria-hidden>
          <DotGrid
            dotSize={5}
            gap={22}
            baseColor={dots.base}
            activeColor={dots.active}
            proximity={130}
            shockRadius={reduce ? 0 : 220}
            shockStrength={reduce ? 0 : 4}
            speedTrigger={reduce ? Number.MAX_SAFE_INTEGER : 100}
            resistance={750}
            returnDuration={1.4}
            className="p-0"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-background/10 via-background/40 to-background" />
        </div>
        <div className="container grid items-center gap-14 pb-20 pt-14 sm:pt-20 lg:grid-cols-[1.1fr_1fr] lg:pb-28">
          <div>
            <motion.div
              initial={reduce ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-5 inline-flex items-center gap-2 rounded-full border bg-card/80 px-3 py-1 text-xs font-medium backdrop-blur"
            >
              <span className="size-1.5 rounded-full bg-success" /> Constraint-optimised with OR-Tools CP-SAT
            </motion.div>
            <h1 className="sr-only">Fair, cheat-resistant exam seating in seconds</h1>
            <div aria-hidden>
              <BlurText
                text="Fair, cheat-resistant exam seating in seconds."
                delay={90}
                animateBy="words"
                direction="top"
                className="font-display text-4xl font-semibold leading-[1.08] tracking-tight text-balance sm:text-5xl lg:text-6xl"
              />
            </div>
            <div className="mt-5 flex flex-wrap items-center gap-x-2 gap-y-1 text-lg text-muted-foreground sm:text-xl" aria-hidden>
              <span>Every plan is</span>
              <RotatingText
                texts={["conflict-free.", "unpredictable.", "reproducible.", "accessible."]}
                mainClassName="overflow-hidden rounded-lg bg-primary px-2.5 py-0.5 font-semibold text-primary-foreground"
                staggerFrom="last"
                staggerDuration={0.025}
                splitLevelClassName="overflow-hidden pb-0.5"
                rotationInterval={2400}
                auto={!reduce}
              />
            </div>
            <p className="mt-5 max-w-xl text-muted-foreground">
              Upload candidates, halls and the timetable. SeatWise seats everyone so that no two neighbours - diagonals included -
              write the same paper, then prints the charts, runs attendance at the door and tells every candidate where to sit.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <motion.div whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }}>
                <Button asChild size="lg">
                  <Link to={user ? "/app" : "/login"}>
                    Get started <ArrowRight />
                  </Link>
                </Button>
              </motion.div>
              <motion.div whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }}>
                <Button asChild size="lg" variant="outline">
                  <Link to="/lookup">
                    <Search /> Find my seat
                  </Link>
                </Button>
              </motion.div>
            </div>
          </div>
          <div className="mx-auto w-full max-w-md lg:max-w-none">
            <HeroHall solveSeconds={s?.typical_solve_s} />
          </div>
        </div>
      </section>

      {/* Live benchmark figures */}
      {s && (
        <section className="border-y bg-card/60">
          <div className="container grid gap-8 py-12 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { value: s.conflicts_avoided ?? 0, suffix: "", label: `same-paper neighbours avoided in a ${s.typical_candidates?.toLocaleString()}-candidate sitting, compared with roll order` },
              { value: s.typical_solve_s ?? 0, suffix: " s", label: `to seat ${s.typical_candidates?.toLocaleString()} candidates; ${s.largest_candidates?.toLocaleString()} take ${s.largest_solve_s} s` },
              { value: s.roll_seat_correlation ?? 0, suffix: "", label: "correlation between roll number and seat - nobody can guess where anyone sits" },
              { value: s.runs ?? 0, suffix: "", label: `benchmark runs, every one ${s.all_hard_rules_satisfied ? "meeting every hard rule" : "checked independently"}` },
            ].map((stat) => (
              <div key={stat.label} data-reveal>
                <div className="font-display text-4xl font-semibold tabular text-primary">
                  {reduce ? stat.value.toLocaleString() : <CountUp to={stat.value} separator="," duration={1.6} />}
                  {stat.suffix}
                </div>
                <p className="mt-2 text-sm text-muted-foreground">{stat.label}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* How it works */}
      <section className="container py-20 sm:py-28">
        <div className="mx-auto max-w-2xl text-center" data-reveal>
          <div className="text-sm font-semibold uppercase tracking-wider text-primary">How it works</div>
          <h2 className="mt-2 font-display text-3xl font-semibold sm:text-4xl">From spreadsheets to seats in four steps</h2>
        </div>
        <div className="hiw relative mx-auto mt-14 max-w-3xl">
          <div className="absolute bottom-6 left-[1.35rem] top-6 w-px bg-border" aria-hidden />
          <div className="hiw-line absolute bottom-6 left-[1.35rem] top-6 w-px origin-top bg-primary" aria-hidden />
          <ol className="space-y-10">
            {STEPS.map((step, i) => (
              <li key={step.title} className="hiw-step relative flex gap-6">
                <span className="relative z-10 flex size-11 shrink-0 items-center justify-center rounded-full border-2 border-primary bg-background text-primary">
                  <step.icon className="size-5" />
                </span>
                <div className="pt-1.5">
                  <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Step {i + 1}</div>
                  <h3 className="mt-1 text-xl font-semibold">{step.title}</h3>
                  <p className="mt-2 text-muted-foreground">{step.text}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Features */}
      <section className="border-y bg-muted/30 py-20 sm:py-28">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center" data-reveal>
            <div className="text-sm font-semibold uppercase tracking-wider text-primary">Features</div>
            <h2 className="mt-2 font-display text-3xl font-semibold sm:text-4xl">Everything an exam office needs on one screen</h2>
          </div>
          <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((f) => (
              <motion.div key={f.title} className="feature-card" whileHover={reduce ? undefined : { y: -4 }} transition={{ type: "spring", stiffness: 300, damping: 20 }}>
                <SpotlightCard className="h-full shadow-soft" spotlightColor="rgba(73, 62, 229, 0.12)">
                  <div className="mb-4 flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <f.icon className="size-5" />
                  </div>
                  <h3 className="font-semibold">{f.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{f.text}</p>
                </SpotlightCard>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Cheat resistance */}
      <section className="container grid items-center gap-12 py-20 sm:py-28 lg:grid-cols-2">
        <div data-reveal>
          <div className="text-sm font-semibold uppercase tracking-wider text-primary">Cheat-resistant by construction</div>
          <h2 className="mt-2 font-display text-3xl font-semibold sm:text-4xl">Nobody sits next to their own paper</h2>
          <p className="mt-4 text-muted-foreground">
            SeatWise colours each hall's seat grid so that seats of one colour never touch - not even diagonally - and gives each
            paper its own colour. The solver then decides who sits where inside each colour, keeping close roll numbers apart.
          </p>
          <ul className="mt-6 space-y-3 text-sm">
            {[
              { icon: ShieldCheck, text: "Eight neighbours around every seat checked, aisles respected." },
              { icon: Hash, text: "Neighbours' roll numbers kept at least five apart." },
              { icon: Accessibility, text: "Accessible seats always go to the candidates who need them." },
              { icon: Fingerprint, text: "Seed, inputs and result are fingerprinted; anyone can re-run and compare." },
            ].map((item) => (
              <li key={item.text} className="flex items-start gap-3">
                <item.icon className="mt-0.5 size-4 shrink-0 text-primary" /> {item.text}
              </li>
            ))}
          </ul>
        </div>
        <div data-reveal>
          <ComparisonGrids />
          <p className="mt-3 text-center text-xs text-muted-foreground">Illustration: four papers in a 5 x 6 room.</p>
        </div>
      </section>

      {/* Calls to action */}
      <section className="container pb-20 sm:pb-28">
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-3xl bg-primary p-8 text-primary-foreground sm:p-10" data-reveal>
            <h2 className="font-display text-2xl font-semibold sm:text-3xl">Plan your next exam on SeatWise</h2>
            <p className="mt-3 text-primary-foreground/80">Import the sample data and generate your first plan in under a minute.</p>
            <Button asChild size="lg" variant="secondary" className="mt-6">
              <Link to={user ? "/app" : "/login"}>
                Get started <ArrowRight />
              </Link>
            </Button>
          </div>
          <div className="rounded-3xl border bg-card p-8 sm:p-10" data-reveal>
            <h2 className="font-display text-2xl font-semibold sm:text-3xl">Looking for your seat?</h2>
            <p className="mt-3 text-muted-foreground">Enter your candidate ID to see your hall and seat for every published exam.</p>
            <form onSubmit={findSeat} className="mt-6 flex flex-col gap-2 sm:flex-row">
              <Input value={candidateId} onChange={(e) => setCandidateId(e.target.value)} placeholder="Candidate ID" className="h-12" aria-label="Candidate ID" />
              <Button type="submit" size="lg" className="h-12" disabled={!candidateId.trim()}>
                <Search /> Find my seat
              </Button>
            </form>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
