import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Camera,
  LineChart,
  Route,
  ShieldCheck,
  Sparkles,
  Thermometer,
  Users,
} from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { HeroScene } from "@/components/three/HeroScene";
import { SpotlightCard } from "@/components/motion/SpotlightCard";
import { AnimatedCounter } from "@/components/motion/AnimatedCounter";
import { GradientText } from "@/components/motion/GradientText";
import { Marquee } from "@/components/motion/Marquee";
import { MagneticButton } from "@/components/motion/MagneticButton";
import { ShapBarChart } from "@/components/charts/ShapBarChart";
import { startSmoothScroll, gsap, ScrollTrigger } from "@/lib/smoothScroll";

const STEPS = [
  {
    icon: Camera,
    title: "Photograph the harvest",
    body: "A farmer uploads a photo from the field — no special equipment, just a phone camera.",
  },
  {
    icon: Sparkles,
    title: "AI grades quality",
    body: "Computer-vision features feed a trained classifier that grades A–C or Reject, with an explanation.",
  },
  {
    icon: LineChart,
    title: "Prices are forecast",
    body: "A market model predicts today's price and a 30-day curve from demand, weather and grade.",
  },
  {
    icon: Route,
    title: "Delivery is planned",
    body: "Buyers, routes and the best day to sell are ranked automatically, spoilage risk included.",
  },
];

const FEATURES = [
  { icon: Sparkles, title: "Explainable grading", body: "Every grade ships with the feature contributions behind it — never a black box." },
  { icon: LineChart, title: "Price intelligence", body: "30-day forecasts with confidence bands, tuned to crop, grade and region." },
  { icon: Thermometer, title: "Cold-chain monitoring", body: "Live temperature, humidity and shock telemetry on every shipment in transit." },
  { icon: Route, title: "Delivery optimization", body: "Buyer, route and timing ranked by price, distance, reliability and spoilage risk." },
  { icon: Users, title: "One marketplace", body: "Farmers, buyers and distributors transact on a single, transparent platform." },
  { icon: ShieldCheck, title: "Model transparency", body: "Every model ships a public model card — algorithm, accuracy, and training data." },
];

const TICKER = [
  { crop: "Tomato · Grade A", price: "₹2,471 / quintal" },
  { crop: "Onion · Grade B", price: "₹1,842 / quintal" },
  { crop: "Mango · Grade A", price: "₹4,960 / quintal" },
  { crop: "Wheat · Grade B", price: "₹2,510 / quintal" },
  { crop: "Cotton · Grade A", price: "₹7,330 / quintal" },
  { crop: "Rice · Grade A", price: "₹3,120 / quintal" },
];

const SAMPLE_SHAP = [
  { feature: "color_uniformity", contribution: 0.41 },
  { feature: "blemish_ratio", contribution: -0.22 },
  { feature: "texture_homogeneity", contribution: 0.18 },
  { feature: "size_score", contribution: 0.12 },
  { feature: "edge_density", contribution: -0.08 },
];

export function Landing() {
  const navigate = useNavigate();
  const stepsRef = useRef<HTMLDivElement>(null);
  const featuresRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stop = startSmoothScroll();

    const ctx = gsap.context(() => {
      if (stepsRef.current) {
        gsap.utils.toArray<HTMLElement>(".how-step").forEach((el, i) => {
          gsap.fromTo(
            el,
            { opacity: 0, y: 40 },
            {
              opacity: 1,
              y: 0,
              duration: 0.6,
              ease: "power3.out",
              delay: i * 0.05,
              scrollTrigger: { trigger: el, start: "top 82%" },
            }
          );
        });
      }
      if (featuresRef.current) {
        gsap.utils.toArray<HTMLElement>(".feature-card").forEach((el, i) => {
          gsap.fromTo(
            el,
            { opacity: 0, y: 24 },
            {
              opacity: 1,
              y: 0,
              duration: 0.5,
              ease: "power2.out",
              delay: (i % 3) * 0.08,
              scrollTrigger: { trigger: el, start: "top 88%" },
            }
          );
        });
      }
    });

    return () => {
      ctx.revert();
      ScrollTrigger.getAll().forEach((t) => t.kill());
      stop();
    };
  }, []);

  return (
    <div className="bg-sand-50">
      <Navbar />

      {/* HERO */}
      <section className="relative min-h-screen flex items-center overflow-hidden pt-16">
        <div className="absolute inset-0 h-full w-full">
          <HeroScene />
        </div>
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-sand-50/10 to-sand-50" />

        <div className="relative mx-auto max-w-7xl px-5 sm:px-8 py-24 w-full">
          <div className="max-w-2xl">
            <motion.span
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-1.5 rounded-full bg-white/80 backdrop-blur px-3 py-1 text-xs font-medium text-brand-700 ring-1 ring-brand-200"
            >
              <Sparkles size={12} /> AI quality grading · price intelligence · smart delivery
            </motion.span>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="font-display text-5xl sm:text-6xl font-semibold text-ink-900 mt-5 leading-[1.05]"
            >
              Move every harvest with <GradientText>certainty</GradientText>, not guesswork.
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-lg text-ink-600 mt-5 max-w-lg"
            >
              CropSight grades crop quality from a photo, forecasts the price it should fetch, and tells you
              exactly who to sell to and when — explained, not black-boxed.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="mt-8 flex items-center gap-4"
            >
              <MagneticButton onClick={() => navigate("/signup")}>
                Get started <ArrowRight size={16} className="ml-1" />
              </MagneticButton>
              <button onClick={() => navigate("/login")} className="text-sm font-semibold text-ink-700 hover:text-ink-900">
                Log in →
              </button>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.45 }}
            className="mt-20 grid grid-cols-2 sm:grid-cols-4 gap-6 max-w-2xl"
          >
            <Stat value={38400} suffix="+" label="Crops graded" />
            <Stat value={17} suffix="%" prefix="+" label="Avg. price uplift" />
            <Stat value={92} suffix="%" label="Grading accuracy" />
            <Stat value={2400} suffix="+" label="Farmers onboarded" />
          </motion.div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how-it-works" ref={stepsRef} className="py-28 bg-white border-y border-ink-100">
        <div className="mx-auto max-w-7xl px-5 sm:px-8">
          <div className="max-w-xl mb-16">
            <p className="text-sm font-semibold text-brand-600 mb-2">How it works</p>
            <h2 className="font-display text-3xl sm:text-4xl font-semibold text-ink-900">From field photo to sold crop, in four steps.</h2>
          </div>
          <div className="grid md:grid-cols-4 gap-6">
            {STEPS.map((s, i) => (
              <div key={s.title} className="how-step relative rounded-2xl border border-ink-100 p-6 bg-sand-50">
                <span className="text-xs font-semibold text-ink-400">{String(i + 1).padStart(2, "0")}</span>
                <s.icon className="text-brand-600 my-3" size={22} />
                <h3 className="font-semibold text-ink-900">{s.title}</h3>
                <p className="text-sm text-ink-500 mt-1.5 leading-relaxed">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" ref={featuresRef} className="py-28">
        <div className="mx-auto max-w-7xl px-5 sm:px-8">
          <div className="max-w-xl mb-16">
            <p className="text-sm font-semibold text-brand-600 mb-2">Platform</p>
            <h2 className="font-display text-3xl sm:text-4xl font-semibold text-ink-900">Everything the supply chain needed to be told, automatically.</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-5">
            {FEATURES.map((f) => (
              <div key={f.title} className="feature-card">
                <SpotlightCard className="h-full">
                  <f.icon className="text-brand-600" size={22} />
                  <h3 className="font-semibold text-ink-900 mt-3">{f.title}</h3>
                  <p className="text-sm text-ink-500 mt-1.5 leading-relaxed">{f.body}</p>
                </SpotlightCard>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* EXPLAINABLE AI DEMO */}
      <section id="intelligence" className="py-28 bg-brand-950 text-white">
        <div className="mx-auto max-w-7xl px-5 sm:px-8 grid lg:grid-cols-2 gap-14 items-center">
          <div>
            <p className="text-sm font-semibold text-brand-300 mb-2">Explainable AI</p>
            <h2 className="font-display text-3xl sm:text-4xl font-semibold">Every score comes with a reason.</h2>
            <p className="text-brand-200 mt-4 leading-relaxed max-w-md">
              Both the quality classifier and the price model are wrapped in SHAP explainability, so a farmer sees
              exactly which features pushed a grade or a price up or down — not just the number.
            </p>
          </div>
          <div className="rounded-2xl bg-white p-6">
            <p className="text-sm font-semibold text-ink-700 mb-2">Sample: why this crop was graded A</p>
            <ShapBarChart items={SAMPLE_SHAP} />
          </div>
        </div>
      </section>

      {/* TICKER */}
      <section className="py-14 bg-sand-100 border-y border-ink-100">
        <Marquee>
          {TICKER.map((t) => (
            <span key={t.crop} className="flex items-center gap-3 text-ink-700 font-medium whitespace-nowrap">
              {t.crop} <span className="text-brand-700 font-semibold">{t.price}</span>
              <span className="text-ink-300">•</span>
            </span>
          ))}
        </Marquee>
      </section>

      {/* CTA */}
      <section className="py-28">
        <div className="mx-auto max-w-4xl px-5 sm:px-8 text-center">
          <h2 className="font-display text-4xl font-semibold text-ink-900">Ready to sell smarter?</h2>
          <p className="text-ink-500 mt-4 max-w-md mx-auto">Set up your account and grade your first crop in under two minutes.</p>
          <div className="mt-8 flex justify-center">
            <MagneticButton onClick={() => navigate("/signup")}>
              Get started free <ArrowRight size={16} className="ml-1" />
            </MagneticButton>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}

function Stat({ value, suffix = "", prefix = "", label }: { value: number; suffix?: string; prefix?: string; label: string }) {
  return (
    <div>
      <p className="font-display text-3xl font-semibold text-ink-900">
        <AnimatedCounter value={value} suffix={suffix} prefix={prefix} />
      </p>
      <p className="text-xs text-ink-500 mt-1">{label}</p>
    </div>
  );
}
