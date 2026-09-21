import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import {
  ArrowRight,
  BadgeCheck,
  ClipboardCheck,
  Columns2,
  FileSearch,
  FileText,
  Gauge,
  Languages,
  Layers,
  MessageSquareText,
  ScanSearch,
  ShieldAlert,
  Sparkles,
  Upload,
} from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { useEffect, useRef } from "react";
import { Link } from "react-router";

import { Logo, LogoMark } from "@/components/brand/Logo";
import Aurora from "@/components/reactbits/Aurora";
import BlurText from "@/components/reactbits/BlurText";
import ShinyText from "@/components/reactbits/ShinyText";
import SpotlightCard from "@/components/reactbits/SpotlightCard";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { useTheme } from "@/lib/theme";

gsap.registerPlugin(ScrollTrigger);

const STEPS = [
  {
    icon: Upload,
    title: "Upload your policy wording",
    text: "Drop in the PDF your insurer gave you. PolicyLens splits it into sections and clauses and keeps every page viewable.",
  },
  {
    icon: Sparkles,
    title: "Get your Policy Card",
    text: "Sum insured, deductible, co-pay, room rent, waiting periods, sub-limits and key exclusions - each value linked to its clause and page.",
  },
  {
    icon: MessageSquareText,
    title: "Ask in plain words",
    text: "Answers come only from your policy, cite the exact clause, and say “not covered in this policy” instead of guessing.",
  },
  {
    icon: ClipboardCheck,
    title: "Claim with confidence",
    text: "Describe a treatment and get a coverage verdict, eligibility checks, a document checklist and the claim steps.",
  },
];

const FEATURES = [
  { icon: FileSearch, title: "Clause-level parsing", text: "Two-column layouts, tables and exclusion codes are read into numbered clauses with page positions." },
  { icon: Sparkles, title: "Policy Card", text: "Key terms extracted automatically, every value verified against a quote from the policy text." },
  { icon: MessageSquareText, title: "Cited answers", text: "Every sentence points to its clause and page. Click a citation to see it highlighted in the PDF." },
  { icon: Layers, title: "Hybrid retrieval", text: "Keyword search and semantic embeddings are fused, then re-ranked, to find the right clause." },
  { icon: ClipboardCheck, title: "Claim Copilot", text: "Covered, partly covered or not covered - with reasons, a checklist and step-by-step procedure." },
  { icon: Columns2, title: "Plan comparison", text: "Two policies side by side: limits, waiting periods, exclusions and the real trade-offs." },
  { icon: ShieldAlert, title: "Risk highlights", text: "Long waits, sub-limits, co-pay traps and room-rent deductions flagged by severity." },
  { icon: Languages, title: "English, हिन्दी, తెలుగు", text: "Ask and read answers in your language; the clause quotes stay in the original English." },
  { icon: Gauge, title: "Faithfulness score", text: "An independent model checks each answer against the cited text and shows how well it holds up." },
];

function useSmoothScroll() {
  const reduce = useReducedMotion();
  useEffect(() => {
    if (reduce) return;
    const lenis = new Lenis({ duration: 1.1, smoothWheel: true });
    lenis.on("scroll", ScrollTrigger.update);
    const tick = (time: number) => lenis.raf(time * 1000);
    gsap.ticker.add(tick);
    gsap.ticker.lagSmoothing(0);
    return () => {
      gsap.ticker.remove(tick);
      lenis.destroy();
    };
  }, [reduce]);
}

function HowItWorks() {
  const root = useRef<HTMLElement>(null);
  const reduce = useReducedMotion();
  useEffect(() => {
    if (reduce || !root.current) return;
    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".hiw-progress",
        { scaleY: 0 },
        { scaleY: 1, ease: "none", scrollTrigger: { trigger: ".hiw-list", start: "top 70%", end: "bottom 60%", scrub: 0.6 } },
      );
      gsap.utils.toArray<HTMLElement>(".hiw-step").forEach((step) => {
        gsap.fromTo(
          step,
          { opacity: 0, x: -24 },
          { opacity: 1, x: 0, duration: 0.7, ease: "power2.out", scrollTrigger: { trigger: step, start: "top 80%" } },
        );
        gsap.fromTo(
          step.querySelector(".hiw-dot"),
          { scale: 0.4, backgroundColor: "var(--muted)" },
          { scale: 1, backgroundColor: "var(--primary)", scrollTrigger: { trigger: step, start: "top 70%", end: "top 55%", scrub: true } },
        );
      });
    }, root);
    return () => ctx.revert();
  }, [reduce]);

  return (
    <section ref={root} id="how-it-works" className="mx-auto max-w-5xl px-4 py-24 sm:px-6">
      <div className="mb-14 text-center">
        <p className="mb-2 text-sm font-semibold uppercase tracking-widest text-primary">How it works</p>
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">From a 50-page PDF to a clear answer</h2>
      </div>
      <div className="hiw-list relative ml-3 sm:ml-6">
        <div className="absolute bottom-2 left-[15px] top-2 w-0.5 rounded bg-border" />
        <div className="hiw-progress absolute bottom-2 left-[15px] top-2 w-0.5 origin-top rounded bg-primary" />
        <ol className="space-y-12">
          {STEPS.map(({ icon: Icon, title, text }, i) => (
            <li key={title} className="hiw-step relative flex gap-6 pl-0">
              <span className="hiw-dot relative z-10 grid size-8 shrink-0 place-items-center rounded-full bg-primary text-sm font-bold text-primary-foreground ring-4 ring-background">
                {i + 1}
              </span>
              <div className="flex-1 rounded-2xl border bg-card p-5 shadow-sm">
                <div className="mb-2 flex items-center gap-2">
                  <Icon className="size-5 text-primary" />
                  <h3 className="text-lg font-semibold">{title}</h3>
                </div>
                <p className="text-muted-foreground">{text}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function Features() {
  const root = useRef<HTMLElement>(null);
  const reduce = useReducedMotion();
  useEffect(() => {
    if (reduce || !root.current) return;
    const ctx = gsap.context(() => {
      gsap.set(".feature-card", { opacity: 0, y: 32 });
      ScrollTrigger.batch(".feature-card", {
        start: "top 88%",
        onEnter: (batch) => gsap.to(batch, { opacity: 1, y: 0, duration: 0.6, ease: "power2.out", stagger: 0.08 }),
      });
    }, root);
    return () => ctx.revert();
  }, [reduce]);

  return (
    <section ref={root} id="features" className="border-y bg-muted/30">
      <div className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
        <div className="mb-12 max-w-2xl">
          <p className="mb-2 text-sm font-semibold uppercase tracking-widest text-primary">Features</p>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Everything your policy says - and what it means for your claim</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <motion.div key={title} className="feature-card" whileHover={{ y: -4 }} transition={{ type: "spring", stiffness: 300, damping: 24 }}>
              <SpotlightCard className="h-full">
                <div className="mb-4 grid size-10 place-items-center rounded-xl bg-primary/10 text-primary">
                  <Icon className="size-5" />
                </div>
                <h3 className="mb-1.5 font-semibold">{title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{text}</p>
              </SpotlightCard>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ExampleAnswer() {
  const reduce = useReducedMotion();
  const appear = (delay: number) =>
    reduce ? {} : { initial: { opacity: 0, y: 12 }, animate: { opacity: 1, y: 0 }, transition: { delay, duration: 0.5 } };
  return (
    <div className="relative mx-auto w-full max-w-md">
      <div className="absolute -inset-6 rounded-[2rem] bg-primary/10 blur-2xl" />
      <div className="relative space-y-3 rounded-2xl border bg-card/90 p-4 shadow-xl backdrop-blur">
        <div className="flex items-center gap-2 border-b pb-3 text-xs text-muted-foreground">
          <FileText className="size-4 text-primary" /> Family Health Optima · sample policy
        </div>
        <motion.div {...appear(0.6)} className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-primary px-3.5 py-2 text-sm text-primary-foreground">
          Is cataract surgery covered, and after how long?
        </motion.div>
        <motion.div {...appear(1.3)} className="flex gap-2">
          <LogoMark className="size-7" />
          <div className="space-y-2 rounded-2xl rounded-tl-md border bg-background p-3 text-sm">
            <p>
              Yes. Cataract is on the list of specified diseases, so it is covered after{" "}
              <strong>24 months of continuous cover</strong>
              <span className="mx-1 inline-grid size-5 place-items-center rounded-md bg-primary/10 text-[11px] font-semibold text-primary">1</span>
            </p>
            <div className="flex items-center gap-1.5 rounded-lg border bg-muted/40 px-2 py-1.5 text-xs text-muted-foreground">
              <span className="grid size-4 place-items-center rounded bg-primary/10 text-[10px] font-semibold text-primary">1</span>
              Excl02 · Specified disease / procedure waiting period · p. 28
            </div>
          </div>
        </motion.div>
        <motion.div {...appear(2)} className="flex items-center gap-2 pl-9 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1 rounded-full border border-success/30 bg-success/10 px-2 py-0.5 font-medium text-success">
            <BadgeCheck className="size-3.5" /> Supported by the cited clause
          </span>
        </motion.div>
      </div>
    </div>
  );
}

export default function Landing() {
  const { user } = useAuth();
  const { resolvedTheme } = useTheme();
  useSmoothScroll();

  return (
    <div className="min-h-dvh bg-background">
      <header className="fixed inset-x-0 top-0 z-40 border-b border-transparent bg-background/70 backdrop-blur supports-[backdrop-filter]:bg-background/50">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link to="/" aria-label="PolicyLens home">
            <Logo />
          </Link>
          <nav className="hidden items-center gap-6 text-sm text-muted-foreground md:flex" aria-label="Sections">
            <a href="#how-it-works" className="hover:text-foreground">
              How it works
            </a>
            <a href="#features" className="hover:text-foreground">
              Features
            </a>
            <a href="#trust" className="hover:text-foreground">
              Why trust it
            </a>
          </nav>
          <div className="flex items-center gap-2">
            {user ? (
              <Button asChild>
                <Link to="/app">
                  Open app <ArrowRight />
                </Link>
              </Button>
            ) : (
              <>
                <Button asChild variant="ghost" className="hidden sm:inline-flex">
                  <Link to="/login">Sign in</Link>
                </Button>
                <Button asChild>
                  <Link to="/register">Get started</Link>
                </Button>
              </>
            )}
          </div>
        </div>
      </header>

      <section className="relative overflow-hidden pb-20 pt-28 sm:pt-32">
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-teal-50 via-background to-background dark:from-teal-950/40" />
        <Aurora
          className="absolute inset-x-0 top-0 -z-10 h-[520px] opacity-70 dark:opacity-60"
          colorStops={resolvedTheme === "dark" ? ["#0f766e", "#14b8a6", "#0369a1"] : ["#5eead4", "#99f6e4", "#7dd3fc"]}
          amplitude={0.9}
          blend={0.55}
        />
        <div className="bg-grid absolute inset-0 -z-10 opacity-40 [mask-image:radial-gradient(ellipse_at_top,black,transparent_70%)]" />
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 sm:px-6 lg:grid-cols-[1.1fr_1fr]">
          <div className="space-y-6">
            <motion.span
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="inline-flex items-center gap-2 rounded-full border bg-card/80 px-3 py-1 text-xs font-medium text-muted-foreground backdrop-blur"
            >
              <ScanSearch className="size-3.5 text-primary" />
              <ShinyText text="For health-insurance policyholders in India" className="text-foreground" />
            </motion.span>
            <BlurText
              as="h1"
              text="Understand your health insurance, clause by clause."
              className="text-balance text-4xl font-extrabold leading-[1.08] tracking-tight sm:text-5xl lg:text-6xl"
              highlight={["clause", "clause."]}
              highlightClassName="text-primary"
              delay={70}
            />
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              className="max-w-xl text-lg text-muted-foreground"
            >
              PolicyLens reads your own policy wording, answers questions with the exact clause and page, flags the fine print that costs money,
              and walks you through your claim.
            </motion.p>
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.8 }} className="flex flex-wrap gap-3">
              <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.98 }}>
                <Button asChild size="lg" className="h-12 px-6 text-base shadow-lg shadow-primary/25">
                  <Link to={user ? "/app" : "/register"}>
                    Get started <ArrowRight />
                  </Link>
                </Button>
              </motion.div>
              <Button asChild size="lg" variant="outline" className="h-12 bg-background/60 px-6 text-base">
                <Link to="/login">Try the demo</Link>
              </Button>
            </motion.div>
            <p className="text-xs text-muted-foreground">Runs on your computer. Your policies stay in your own library.</p>
          </div>
          <ExampleAnswer />
        </div>
      </section>

      <HowItWorks />
      <Features />

      <section id="trust" className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <div className="space-y-4">
            <p className="text-sm font-semibold uppercase tracking-widest text-primary">Why trust it</p>
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Grounded in your document, checked twice</h2>
            <p className="text-muted-foreground">
              General chatbots answer from what “most policies” do. PolicyLens only answers from the clauses of your policy, removes any citation
              that doesn't point to a retrieved clause, and has a separate model score how well every statement is supported.
            </p>
            <ul className="space-y-3 text-sm">
              {[
                "Answers cite the clause and page - one click shows it highlighted in the PDF",
                "Says “not covered in this policy” when the wording is silent",
                "Every Policy Card value is matched against a quote from the text",
                "Accuracy, faithfulness and response time are measured and shown in the app",
              ].map((x) => (
                <li key={x} className="flex gap-2">
                  <BadgeCheck className="mt-0.5 size-4 shrink-0 text-primary" /> {x}
                </li>
              ))}
            </ul>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              { lang: "English", word: "Waiting period" },
              { lang: "हिन्दी", word: "प्रतीक्षा अवधि" },
              { lang: "తెలుగు", word: "వేచి ఉండే సమయం" },
            ].map((x, i) => (
              <motion.div
                key={x.lang}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                whileHover={{ y: -4 }}
                className="rounded-2xl border bg-card p-5 text-center shadow-sm"
              >
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{x.lang}</div>
                <div className="mt-2 text-lg font-semibold">{x.word}</div>
              </motion.div>
            ))}
            <p className="text-center text-sm text-muted-foreground sm:col-span-3">Ask and read answers in English, Hindi or Telugu.</p>
          </div>
        </div>
      </section>

      <section className="px-4 pb-24 sm:px-6">
        <div className="relative mx-auto max-w-5xl overflow-hidden rounded-3xl bg-gradient-to-br from-teal-700 via-teal-800 to-slate-900 px-6 py-14 text-center text-white sm:px-12">
          <div className="bg-grid absolute inset-0 opacity-15" />
          <div className="relative space-y-5">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Know what you're covered for - before you need it</h2>
            <p className="mx-auto max-w-xl text-teal-50/85">Upload your policy and ask your first question in under two minutes.</p>
            <motion.div whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.98 }} className="inline-block">
              <Button asChild size="lg" variant="secondary" className="h-12 px-7 text-base">
                <Link to={user ? "/app/policies" : "/register"}>
                  Get started free <ArrowRight />
                </Link>
              </Button>
            </motion.div>
          </div>
        </div>
      </section>

      <footer className="border-t">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="space-y-1">
            <Logo />
            <p className="text-xs">Clear answers from your own health-insurance policy.</p>
          </div>
          <nav className="flex flex-wrap gap-5" aria-label="Footer">
            <Link to="/login" className="hover:text-foreground">
              Sign in
            </Link>
            <Link to="/register" className="hover:text-foreground">
              Create account
            </Link>
            <a href="#features" className="hover:text-foreground">
              Features
            </a>
          </nav>
          <p className="text-xs">© {new Date().getFullYear()} PolicyLens. Guidance only - your insurer makes the final claim decision.</p>
        </div>
      </footer>
    </div>
  );
}
