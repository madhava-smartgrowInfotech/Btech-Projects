import { ArrowRight, BrainCircuit, ClipboardCheck, FileSearch, Route, UploadCloud } from "lucide-react";
import { Link } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { ExampleAnswer } from "@/components/landing/ExampleAnswer";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { StatsStrip } from "@/components/landing/StatsStrip";
import { FadeIn, Marquee, Parallax, Reveal, SlideUp, SmoothScroll } from "@/components/motion";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { ThemeToggle } from "@/components/ui/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useAuth } from "@/lib/auth";

const FEATURES = [
  {
    icon: UploadCloud,
    title: "Document analysis",
    text: "PDF, DOCX and TXT are read, cleaned and split into passages. Subject, unit and chapter lines plus TF-IDF keywords become the topics of your knowledge repository.",
  },
  {
    icon: FileSearch,
    title: "Answers from your notes",
    text: "Ask a question and the best-matching passages of your own documents are retrieved. Turn on a Claude key for written answers, or stay fully offline.",
  },
  {
    icon: ClipboardCheck,
    title: "Auto-generated quizzes",
    text: "Key terms are blanked out of sentences in your document to make multiple-choice questions, so you practise exactly what you uploaded.",
  },
  {
    icon: Route,
    title: "Adaptive roadmap",
    text: "Quiz accuracy is tracked per topic. The weakest topics rise to the top as High priority, so you know what to revise next.",
  },
];

const TAGS = ["Syllabi", "Lecture notes", "Question banks", "Timetables", "PDF", "DOCX", "TXT", "Data Structures", "DBMS", "Machine Learning"];

export default function Landing() {
  const { user } = useAuth();
  return (
    <div className="relative">
      <SmoothScroll />
      <AuroraBackground />

      <header className="sticky top-0 z-30 px-3 pt-3">
        <div className="glass mx-auto flex h-14 max-w-6xl items-center gap-2 rounded-2xl px-3 sm:px-4">
          <Link to="/" aria-label="Adaptive Learning home">
            <Logo />
          </Link>
          <nav aria-label="Page sections" className="ml-6 hidden items-center gap-5 text-sm text-muted-foreground md:flex">
            <a href="#features" className="transition-colors hover:text-foreground">
              Features
            </a>
            <a href="#how-it-works" className="transition-colors hover:text-foreground">
              How it works
            </a>
          </nav>
          <div className="ml-auto flex items-center gap-1.5">
            <ThemeToggle />
            {user ? (
              <Button asChild size="sm">
                <Link to="/app">Open app</Link>
              </Button>
            ) : (
              <>
                <Button asChild variant="ghost" size="sm" className="hidden sm:inline-flex">
                  <Link to="/login">Sign in</Link>
                </Button>
                <Button asChild size="sm">
                  <Link to="/register">Get started</Link>
                </Button>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="overflow-x-clip">
        <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-20 pt-14 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:pt-24">
          <div className="space-y-6">
            <SlideUp>
              <Badge tone="violet" className="gap-1.5 px-3 py-1 text-xs">
                <BrainCircuit /> Adaptive Learning Intelligence Platform
              </Badge>
            </SlideUp>
            <SlideUp delay={0.08}>
              <h1 className="font-display text-4xl font-semibold leading-[1.05] tracking-tight text-balance sm:text-5xl lg:text-6xl">
                Study smarter from <span className="text-gradient">your own notes</span>
              </h1>
            </SlideUp>
            <SlideUp delay={0.16}>
              <p className="max-w-xl text-lg text-muted-foreground">
                Upload your syllabus and lecture notes, ask questions that are answered from them, practise with auto-generated quizzes and let your results
                build a revision roadmap.
              </p>
            </SlideUp>
            <SlideUp delay={0.24} className="flex flex-wrap items-center gap-3">
              <Button asChild size="lg">
                <Link to={user ? "/app" : "/register"}>
                  {user ? "Go to dashboard" : "Start free"} <ArrowRight />
                </Link>
              </Button>
              {!user && (
                <Button asChild size="lg" variant="secondary">
                  <Link to="/login">I already have an account</Link>
                </Button>
              )}
            </SlideUp>
          </div>
          <FadeIn delay={0.3}>
            <Parallax offset={24}>
              <ExampleAnswer />
            </Parallax>
          </FadeIn>
        </section>

        <div className="pb-16">
          <Marquee speed={45}>
            {TAGS.map((t) => (
              <span key={t} className="glass rounded-full px-4 py-1.5 text-sm text-muted-foreground">
                {t}
              </span>
            ))}
          </Marquee>
        </div>

        <section id="features" className="mx-auto max-w-6xl scroll-mt-24 px-4 py-16 sm:px-6">
          <div className="mb-10 max-w-xl space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">What you get</p>
            <h2 className="font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
              One place for your notes, questions, quizzes and plan
            </h2>
          </div>
          <Reveal className="grid gap-4 sm:grid-cols-2">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <Card key={title} data-reveal interactive className="space-y-3 p-6">
                <span className="grid size-11 place-items-center rounded-2xl bg-grad-primary text-white shadow-[0_10px_26px_-10px_rgba(124,92,255,0.9)]">
                  <Icon className="size-5" />
                </span>
                <h3 className="font-display text-lg font-semibold">{title}</h3>
                <p className="text-muted-foreground">{text}</p>
              </Card>
            ))}
          </Reveal>
        </section>

        <HowItWorks />

        <div className="py-16">
          <StatsStrip />
        </div>

        <section className="mx-auto max-w-4xl px-4 pb-24 sm:px-6">
          <Reveal>
            <div className="glass-strong relative overflow-hidden rounded-3xl px-6 py-12 text-center sm:px-12">
              <div aria-hidden className="absolute -inset-10 bg-grad-primary opacity-15 blur-3xl" />
              <div className="relative space-y-5">
                <h2 className="font-display text-3xl font-semibold tracking-tight text-balance sm:text-4xl">
                  Upload your first document and see what to revise
                </h2>
                <p className="mx-auto max-w-lg text-muted-foreground">The sample notes in the project let you try every feature in a couple of minutes.</p>
                <Button asChild size="lg">
                  <Link to={user ? "/app/upload" : "/register"}>
                    {user ? "Upload material" : "Create your account"} <ArrowRight />
                  </Link>
                </Button>
              </div>
            </div>
          </Reveal>
        </section>
      </main>

      <footer className="border-t border-[var(--glass-border)] px-4 py-8 text-center text-sm text-muted-foreground">
        Adaptive Learning Intelligence Platform &mdash; B.Tech final year project
      </footer>
    </div>
  );
}
