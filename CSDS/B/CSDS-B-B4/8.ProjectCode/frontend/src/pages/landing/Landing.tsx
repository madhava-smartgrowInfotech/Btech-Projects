import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion, useReducedMotion } from "motion/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import {
  ArrowRight,
  BadgeCheck,
  BarChart3,
  BellRing,
  Brain,
  Clock3,
  FlaskConical,
  Languages,
  MessageCircleQuestion,
  MessageSquareWarning,
  Pause,
  Play,
  QrCode,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/brand/Logo";
import { ThemeMenu } from "@/components/layout/AppLayout";
import Aurora from "@/components/reactbits/Aurora";
import BlurText from "@/components/reactbits/BlurText";
import CountUp from "@/components/reactbits/CountUp";
import RotatingText from "@/components/reactbits/RotatingText";
import ShinyText from "@/components/reactbits/ShinyText";
import SpotlightCard from "@/components/reactbits/SpotlightCard";
import { api } from "@/lib/api";
import { LANGUAGES, useI18n, type Language } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import type { MessageKey } from "@/locales/en";

gsap.registerPlugin(ScrollTrigger);

interface Highlights {
  languages: number;
  risk?: { pr_auc: number; scams_checked: number; scams_held: number; genuine_straight_through: number; test_payments: number };
  sms?: { f1: number; test_messages: number };
  behaviour?: { roc_auc: number };
}

const STEPS: { icon: typeof ShieldCheck; title: MessageKey; body: MessageKey }[] = [
  { icon: ShieldCheck, title: "landing.how.1.title", body: "landing.how.1.body" },
  { icon: MessageCircleQuestion, title: "landing.how.2.title", body: "landing.how.2.body" },
  { icon: Clock3, title: "landing.how.3.title", body: "landing.how.3.body" },
  { icon: Languages, title: "landing.how.4.title", body: "landing.how.4.body" },
];

const FEATURES: { icon: typeof ShieldCheck; key: string }[] = [
  { icon: Brain, key: "f2" },
  { icon: BadgeCheck, key: "f3" },
  { icon: MessageSquareWarning, key: "f4" },
  { icon: MessageCircleQuestion, key: "f5" },
  { icon: Clock3, key: "f6" },
  { icon: Sparkles, key: "f7" },
  { icon: Languages, key: "f8" },
  { icon: QrCode, key: "f9" },
  { icon: BarChart3, key: "f10" },
  { icon: FlaskConical, key: "f1" },
];

/** Smooth scrolling (Lenis) wired into GSAP's ticker so ScrollTrigger stays in sync. */
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

function VoiceSample() {
  const { t } = useI18n();
  const [playing, setPlaying] = useState<Language | null>(null);
  const audio = useRef<HTMLAudioElement | null>(null);
  useEffect(() => () => audio.current?.pause(), []);
  const play = (lang: Language) => {
    audio.current?.pause();
    if (playing === lang) {
      setPlaying(null);
      return;
    }
    const el = new Audio(`/api/public/guide/home.mp3?lang=${lang}`);
    el.onended = () => setPlaying(null);
    el.onerror = () => setPlaying(null);
    audio.current = el;
    setPlaying(lang);
    void el.play().catch(() => setPlaying(null));
  };
  return (
    <div className="flex flex-wrap gap-2">
      {LANGUAGES.map((l) => (
        <Button key={l.code} variant={playing === l.code ? "default" : "outline"} onClick={() => play(l.code)} aria-pressed={playing === l.code} className="gap-2">
          {playing === l.code ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          {t("landing.voice.play", { lang: l.native })}
        </Button>
      ))}
    </div>
  );
}

function HeroMock() {
  const { t } = useI18n();
  const reduce = useReducedMotion();
  const rows: MessageKey[] = ["landing.mock.r1", "landing.mock.r2", "landing.mock.r3"];
  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 30, rotate: -2 }}
      animate={{ opacity: 1, y: 0, rotate: 0 }}
      transition={{ delay: 0.5, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
      className="relative mx-auto w-full max-w-sm rounded-[2rem] border border-white/15 bg-white/10 p-4 shadow-2xl backdrop-blur-xl"
      aria-label={t("landing.mock.aria")}
    >
      <div className="rounded-3xl bg-[#0b1215]/90 p-5 text-white">
        <div className="flex items-center justify-between text-xs text-white/60">
          <span>{t("landing.mock.example")}</span>
          <span className="rounded-full bg-amber-400/15 px-2 py-0.5 text-amber-200">{t("common.sandbox_short")}</span>
        </div>
        <div className="mt-4 flex items-center justify-between">
          <div>
            <p className="font-medium">{t("landing.mock.payee")}</p>
            <p className="text-xs text-white/60">{t("landing.mock.payee_sub")}</p>
          </div>
          <p className="font-display text-2xl font-semibold">₹25,000</p>
        </div>
        <div className="mt-4 flex items-center gap-3 rounded-2xl bg-rose-500/15 p-3">
          <ShieldAlert className="h-8 w-8 shrink-0 text-rose-300" />
          <div>
            <p className="font-semibold text-rose-200">{t("pay.headline.high")}</p>
            <p className="text-xs text-white/70">{t("risk.score")} 97 / 100</p>
          </div>
        </div>
        <ul className="mt-3 space-y-2">
          {rows.map((r, i) => (
            <motion.li
              key={r}
              initial={reduce ? false : { opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 1 + i * 0.25 }}
              className="flex gap-2 rounded-xl bg-white/5 px-3 py-2 text-xs text-white/85"
            >
              <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-300" />
              {t(r)}
            </motion.li>
          ))}
        </ul>
        <motion.div
          initial={reduce ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.9 }}
          className="mt-4 flex items-center justify-between rounded-2xl border border-amber-300/30 bg-amber-300/10 px-3 py-2.5 text-xs text-amber-100"
        >
          <span className="flex items-center gap-2">
            <Clock3 className="h-4 w-4" />
            {t("landing.mock.hold")}
          </span>
          <span className="font-mono">29:58</span>
        </motion.div>
      </div>
    </motion.div>
  );
}

export default function Landing() {
  const { t, lang, setLang } = useI18n();
  const reduce = useReducedMotion();
  const root = useRef<HTMLDivElement>(null);
  const [scrolled, setScrolled] = useState(false);
  const highlights = useQuery({ queryKey: ["public", "highlights"], queryFn: async () => (await api.get<Highlights>("/public/highlights")).data, staleTime: 600_000 });
  const h = highlights.data;
  useSmoothScroll(!reduce);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (reduce || !root.current) return;
    const ctx = gsap.context(() => {
      gsap.from(".how-step", {
        opacity: 0,
        y: 48,
        duration: 0.8,
        stagger: 0.18,
        ease: "power3.out",
        scrollTrigger: { trigger: "#how", start: "top 70%" },
      });
      gsap.fromTo(".how-line", { scaleY: 0 }, { scaleY: 1, ease: "none", scrollTrigger: { trigger: "#how-steps", start: "top 65%", end: "bottom 60%", scrub: true } });
      ScrollTrigger.batch(".feature-card", {
        start: "top 88%",
        onEnter: (els) => gsap.fromTo(els, { opacity: 0, y: 40 }, { opacity: 1, y: 0, stagger: 0.08, duration: 0.7, ease: "power3.out", overwrite: true }),
      });
      gsap.from(".stat-card", { opacity: 0, y: 24, stagger: 0.1, duration: 0.6, scrollTrigger: { trigger: "#stats", start: "top 85%" } });
      gsap.from(".voice-block", { opacity: 0, x: -40, duration: 0.8, scrollTrigger: { trigger: "#voice", start: "top 75%" } });
    }, root);
    return () => ctx.revert();
  }, [reduce]);

  const stats = [
    { value: h?.risk ? Math.round(h.risk.scams_checked * 1000) / 10 : null, suffix: "%", label: t("landing.stats.scams") },
    { value: h?.risk ? Math.round(h.risk.genuine_straight_through * 1000) / 10 : null, suffix: "%", label: t("landing.stats.genuine") },
    { value: h?.sms ? Math.round(h.sms.f1 * 1000) / 10 : null, suffix: "%", label: t("landing.stats.sms") },
    { value: h?.languages ?? 3, suffix: "", label: t("landing.stats.languages") },
  ];
  const rotating = ["landing.rotate.1", "landing.rotate.2", "landing.rotate.3", "landing.rotate.4", "landing.rotate.5"].map((k) => t(k as MessageKey));

  return (
    <div ref={root} className="min-h-dvh bg-background">
      {/* Header */}
      <header className={cn("fixed inset-x-0 top-0 z-40 transition-all", scrolled ? "border-b bg-background/85 backdrop-blur-xl" : "bg-transparent")}>
        <div className="container flex h-16 items-center gap-3">
          <Link to="/" aria-label="UPI Guardian">
            <Logo className={cn(!scrolled && "[&_span]:text-white")} />
          </Link>
          <nav className={cn("ml-6 hidden items-center gap-5 text-sm md:flex", scrolled ? "text-muted-foreground" : "text-white/75")} aria-label="Sections">
            <a href="#how" className="hover:text-primary">{t("landing.nav.how")}</a>
            <a href="#features" className="hover:text-primary">{t("landing.nav.features")}</a>
            <a href="#voice" className="hover:text-primary">{t("landing.nav.voice")}</a>
            <a href="#stats" className="hover:text-primary">{t("landing.nav.results")}</a>
          </nav>
          <div className="ml-auto flex items-center gap-1">
            <div className={cn("hidden rounded-full border p-0.5 sm:flex", !scrolled && "border-white/20")} role="group" aria-label={t("nav.language")}>
              {LANGUAGES.map((l) => (
                <button
                  key={l.code}
                  onClick={() => setLang(l.code)}
                  className={cn("rounded-full px-2 py-1 text-xs", lang === l.code ? "bg-primary text-primary-foreground" : scrolled ? "text-muted-foreground" : "text-white/75")}
                  aria-pressed={lang === l.code}
                >
                  {l.native}
                </button>
              ))}
            </div>
            <div className={cn(!scrolled && "text-white [&_button]:text-white")}>
              <ThemeMenu />
            </div>
            <Button asChild variant="ghost" className={cn("hidden sm:inline-flex", !scrolled && "text-white hover:bg-white/10 hover:text-white")}>
              <Link to="/login">{t("landing.signin")}</Link>
            </Button>
            <Button asChild>
              <Link to="/register">{t("landing.get_started")}</Link>
            </Button>
          </div>
        </div>
      </header>

      <main id="main">
        {/* Hero */}
        <section className="relative overflow-hidden bg-[#051312] pb-20 pt-28 text-white sm:pb-28 sm:pt-36">
          <div className="pointer-events-none absolute inset-0 opacity-80" aria-hidden>
            {!reduce && <Aurora colorStops={["#0d9488", "#22d3ee", "#f59e0b"]} amplitude={1.1} blend={0.55} speed={0.6} />}
          </div>
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-[#051312]/40 to-[#051312]" aria-hidden />
          <div className="container relative grid items-center gap-12 lg:grid-cols-[1.15fr_1fr]">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs">
                <FlaskConical className="h-3.5 w-3.5 text-amber-300" />
                <ShinyText text={t("landing.badge")} speed={3} color="#cbd5e1" shineColor="#ffffff" />
              </span>
              <h1 className="mt-5 font-display text-4xl font-semibold leading-[1.08] tracking-tight sm:text-6xl">
                <BlurText key={lang} text={t("app.tagline")} delay={90} animateBy="words" direction="top" className="flex flex-wrap" />
              </h1>
              <p className="mt-5 max-w-xl text-lg text-white/75">
                {t("landing.hero.lead")}{" "}
                <span className="inline-flex align-bottom">
                  <RotatingText
                    key={lang}
                    texts={rotating}
                    mainClassName="rounded-lg bg-teal-400/15 px-2 py-0.5 font-semibold text-teal-200 overflow-hidden"
                    staggerFrom="last"
                    initial={{ y: "100%" }}
                    animate={{ y: 0 }}
                    exit={{ y: "-120%" }}
                    staggerDuration={0.02}
                    splitLevelClassName="overflow-hidden"
                    transition={{ type: "spring", damping: 30, stiffness: 400 }}
                    rotationInterval={2600}
                    splitBy="words"
                  />
                </span>
              </p>
              <p className="mt-4 max-w-xl text-white/60">{t("landing.hero.sub")}</p>
              <div className="mt-8 flex flex-wrap gap-3">
                <motion.div whileHover={{ y: -2 }} whileTap={{ scale: 0.97 }}>
                  <Button asChild size="lg" className="h-12 bg-teal-400 px-6 text-[#052321] hover:bg-teal-300">
                    <Link to="/register">
                      {t("landing.get_started")}
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                </motion.div>
                <motion.div whileHover={{ y: -2 }} whileTap={{ scale: 0.97 }}>
                  <Button asChild size="lg" variant="outline" className="h-12 border-white/25 bg-white/5 px-6 text-white hover:bg-white/10 hover:text-white">
                    <Link to="/login">{t("landing.try_demo")}</Link>
                  </Button>
                </motion.div>
              </div>
            </div>
            <HeroMock />
          </div>
        </section>

        {/* Stats */}
        <section id="stats" className="border-b bg-card py-12">
          <div className="container">
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              {stats.map((s) => (
                <div key={s.label} className="stat-card rounded-2xl border bg-background p-5">
                  <p className="font-display text-3xl font-semibold tabular text-primary sm:text-4xl">
                    {s.value === null ? "–" : <CountUp to={s.value} duration={1.6} separator="," />}
                    {s.value !== null && s.suffix}
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">{s.label}</p>
                </div>
              ))}
            </div>
            <p className="mt-4 text-center text-xs text-muted-foreground">{t("landing.stats.note")}</p>
          </div>
        </section>

        {/* How it works */}
        <section id="how" className="py-20 sm:py-28">
          <div className="container max-w-4xl">
            <p className="text-sm font-semibold uppercase tracking-wider text-primary">{t("landing.nav.how")}</p>
            <h2 className="mt-2 font-display text-3xl font-semibold sm:text-4xl">{t("landing.how.title")}</h2>
            <p className="mt-3 max-w-2xl text-muted-foreground">{t("landing.how.sub")}</p>
            <ol id="how-steps" className="relative mt-12 space-y-10 pl-14">
              <span className="absolute left-5 top-2 h-[calc(100%-1rem)] w-px bg-border" aria-hidden />
              <span className="how-line absolute left-5 top-2 h-[calc(100%-1rem)] w-px origin-top bg-primary" aria-hidden />
              {STEPS.map((s, i) => (
                <li key={s.title} className="how-step relative">
                  <span className="absolute -left-14 grid h-10 w-10 place-items-center rounded-full border-2 border-primary bg-background text-primary">
                    <s.icon className="h-5 w-5" />
                  </span>
                  <p className="text-xs font-semibold text-muted-foreground">{t("landing.how.step", { n: i + 1 })}</p>
                  <h3 className="mt-1 font-display text-xl font-semibold">{t(s.title)}</h3>
                  <p className="mt-1.5 max-w-2xl text-muted-foreground">{t(s.body)}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="bg-muted/40 py-20 sm:py-28">
          <div className="container">
            <p className="text-sm font-semibold uppercase tracking-wider text-primary">{t("landing.nav.features")}</p>
            <h2 className="mt-2 max-w-3xl font-display text-3xl font-semibold sm:text-4xl">{t("landing.features.title")}</h2>
            <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
              {FEATURES.map((f) => (
                <motion.div key={f.key} className="feature-card" whileHover={{ y: -4 }} transition={{ type: "spring", stiffness: 300, damping: 20 }}>
                  <SpotlightCard className="h-full !rounded-2xl !border-border !bg-card !p-5" spotlightColor="rgba(20, 184, 166, 0.18)">
                    <span className="grid h-10 w-10 place-items-center rounded-xl bg-primary/10 text-primary">
                      <f.icon className="h-5 w-5" />
                    </span>
                    <h3 className="mt-4 font-display text-base font-semibold text-card-foreground">{t(`landing.feature.${f.key}.title` as MessageKey)}</h3>
                    <p className="mt-1.5 text-sm text-muted-foreground">{t(`landing.feature.${f.key}.body` as MessageKey)}</p>
                  </SpotlightCard>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Voice */}
        <section id="voice" className="py-20 sm:py-28">
          <div className="container grid items-center gap-10 lg:grid-cols-2">
            <div className="voice-block">
              <p className="text-sm font-semibold uppercase tracking-wider text-primary">{t("landing.nav.voice")}</p>
              <h2 className="mt-2 font-display text-3xl font-semibold sm:text-4xl">{t("landing.voice.title")}</h2>
              <p className="mt-3 text-muted-foreground">{t("landing.voice.sub")}</p>
              <div className="mt-6">
                <VoiceSample />
              </div>
            </div>
            <div className="grid gap-3">
              {[
                { icon: Users, key: "landing.voice.p1" as MessageKey },
                { icon: BellRing, key: "landing.voice.p2" as MessageKey },
                { icon: ShieldCheck, key: "landing.voice.p3" as MessageKey },
              ].map((p) => (
                <motion.div key={p.key} whileHover={{ x: 4 }} className="surface flex items-start gap-3 p-4">
                  <p.icon className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
                  <p className="text-sm">{t(p.key)}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="pb-20">
          <div className="container">
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-700 to-[#062a2a] p-8 text-white sm:p-12">
              <div className="pointer-events-none absolute -right-10 -top-10 h-60 w-60 rounded-full bg-amber-400/20 blur-3xl" aria-hidden />
              <h2 className="relative max-w-2xl font-display text-3xl font-semibold">{t("landing.cta.title")}</h2>
              <p className="relative mt-3 max-w-xl text-white/75">{t("landing.cta.sub")}</p>
              <div className="relative mt-6 flex flex-wrap gap-3">
                <Button asChild size="lg" className="bg-white text-brand-900 hover:bg-white/90">
                  <Link to="/register">{t("landing.get_started")}</Link>
                </Button>
                <Button asChild size="lg" variant="outline" className="border-white/30 bg-transparent text-white hover:bg-white/10 hover:text-white">
                  <Link to="/login">{t("landing.try_demo")}</Link>
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-10">
        <div className="container flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
          <div className="max-w-sm">
            <Logo />
            <p className="mt-3 text-sm text-muted-foreground">{t("landing.footer.tagline")}</p>
            <p className="mt-2 text-xs text-muted-foreground">{t("landing.footer.sandbox")}</p>
          </div>
          <nav className="grid grid-cols-2 gap-x-10 gap-y-2 text-sm" aria-label="Footer">
            <a href="#how" className="text-muted-foreground hover:text-primary">{t("landing.nav.how")}</a>
            <Link to="/login" className="text-muted-foreground hover:text-primary">{t("landing.signin")}</Link>
            <a href="#features" className="text-muted-foreground hover:text-primary">{t("landing.nav.features")}</a>
            <Link to="/register" className="text-muted-foreground hover:text-primary">{t("landing.get_started")}</Link>
            <a href="#voice" className="text-muted-foreground hover:text-primary">{t("landing.nav.voice")}</a>
            <a href="/docs" target="_blank" rel="noreferrer" className="text-muted-foreground hover:text-primary">{t("landing.footer.api")}</a>
          </nav>
        </div>
        <p className="container mt-8 text-xs text-muted-foreground">{t("landing.footer.rights", { year: new Date().getFullYear() })}</p>
      </footer>
    </div>
  );
}
