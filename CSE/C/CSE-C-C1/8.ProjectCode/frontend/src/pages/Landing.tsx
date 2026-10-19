import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, CalendarClock, FileSearch, Fingerprint, LayoutDashboard, Link2, Lock, ShieldCheck, Vote } from "lucide-react";
import { Link } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { CountUp } from "@/components/motion/CountUp";
import { MagneticButton } from "@/components/motion/MagneticButton";
import { Marquee } from "@/components/motion/Marquee";
import { Reveal } from "@/components/motion/Reveal";
import { SlideUp } from "@/components/motion/SlideUp";
import { SmoothScroll } from "@/components/motion/SmoothScroll";
import { StatusBadge } from "@/components/domain/common";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { ThemeToggle } from "@/components/ui/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { HOME_BY_ROLE, useAuth } from "@/lib/auth";
import { usePublicOverview } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

const PRIMITIVES = ["AES-256-GCM ballots", "SHA-256 hash chain", "Ed25519 signatures", "Argon2id passwords", "Verhoeff checksum", "Merkle root per block", "2 of 3 validator quorum", "One-time tokens"];

const FEATURES = [
  { icon: Lock, title: "Encrypted ballots", text: "AES-256-GCM with an election-specific key. Identity is stored apart from the ballot, so a record never links a person to a choice." },
  { icon: Link2, title: "Ledger integrity", text: "SHA-256 chained blocks, a Merkle root and a 2 of 3 validator quorum. Any edit breaks every hash after it." },
  { icon: FileSearch, title: "Independent audit", text: "Auditors recompute the chain from genesis, inspect any block and read the audit log, without ever seeing who voted for whom." },
];

function LedgerVisual() {
  const q = usePublicOverview();
  const reduce = useReducedMotion();
  const height = q.data?.ledger.height ?? null;
  const valid = q.data?.ledger.valid;
  const blocks = height ? [height - 3, height - 2, height - 1].filter((n) => n >= 0) : [];
  return (
    <div className="relative mx-auto w-full max-w-md">
      <div aria-hidden className="absolute -inset-8 rounded-[2.5rem] bg-grad-primary opacity-25 blur-3xl" />
      <div className="glass-strong sweep relative space-y-3 rounded-3xl p-4 sm:p-5">
        <div className="flex items-center gap-2 border-b border-[var(--glass-border)] pb-3 text-xs text-muted-foreground">
          <ShieldCheck className="size-4 text-violet-ink" /> Live ledger
          <span className="ml-auto flex items-center gap-1.5">
            {q.isPending ? (
              <Skeleton className="h-4 w-20" />
            ) : q.isError ? (
              <Badge tone="neutral">Offline</Badge>
            ) : (
              <Badge tone={valid ? "success" : "danger"}>{valid ? "Chain valid" : "Integrity warning"}</Badge>
            )}
          </span>
        </div>
        {q.isPending && (
          <div className="space-y-3" role="status" aria-label="Loading ledger">
            {[0, 1, 2].map((i) => <Skeleton key={i} className="h-16 w-full rounded-2xl" />)}
          </div>
        )}
        {q.isError && <p className="py-8 text-center text-sm text-muted-foreground">The ledger is not reachable right now. Start the backend with run.bat.</p>}
        {!q.isPending && !q.isError && blocks.map((n, i) => (
          <motion.div
            key={n}
            initial={{ opacity: 0, y: reduce ? 0 : 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 + i * 0.18, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="relative"
          >
            {i > 0 && <span aria-hidden className="absolute -top-3 left-6 h-3 w-px bg-gradient-to-b from-violet to-cyan" />}
            <div className="flex items-center gap-3 rounded-2xl border border-[var(--glass-border)] bg-[var(--glass)] p-3">
              <span className="grid size-10 place-items-center rounded-xl bg-grad-primary font-display text-sm font-semibold text-white">#{n}</span>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium">Block {n}</div>
                <div className="text-xs text-muted-foreground">{i === blocks.length - 1 ? "Chain tip" : "Linked to the next block by its hash"}</div>
              </div>
              <span className="inline-flex items-center gap-1 text-xs text-success"><ShieldCheck className="size-3.5" /> 2/3 signed</span>
            </div>
          </motion.div>
        ))}
        {!q.isPending && !q.isError && (
          <p className="pt-1 text-center text-xs text-muted-foreground">
            {height} blocks on the chain · {q.data?.votes_cast ?? 0} ballots recorded
          </p>
        )}
      </div>
    </div>
  );
}

function StatsStrip() {
  const q = usePublicOverview();
  const stats = q.data
    ? [
        { label: "Elections", value: q.data.elections.length },
        { label: "Ballots recorded", value: q.data.votes_cast },
        { label: "Blocks on the ledger", value: q.data.ledger.height ?? 0 },
        { label: "Validator nodes", value: q.data.validators },
      ]
    : [];
  return (
    <section aria-label="Live figures" className="mx-auto max-w-6xl px-4 sm:px-6">
      <div className="glass relative overflow-hidden rounded-3xl px-5 py-8 sm:px-8">
        <div aria-hidden className="absolute -top-24 left-1/2 h-48 w-2/3 -translate-x-1/2 rounded-full bg-violet/25 blur-3xl" />
        <div className="relative mb-6 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Live from the running system</p>
        </div>
        {q.isPending ? (
          <div className="relative grid grid-cols-2 gap-6 lg:grid-cols-4" role="status" aria-label="Loading figures">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="space-y-2"><Skeleton className="mx-auto h-9 w-20" /><Skeleton className="mx-auto h-3 w-24" /></div>
            ))}
          </div>
        ) : q.isError ? (
          <p className="relative text-center text-sm text-muted-foreground">Figures appear here once the backend is running.</p>
        ) : (
          <Reveal className="relative grid grid-cols-2 gap-x-4 gap-y-6 lg:grid-cols-4">
            {stats.map((s) => (
              <div key={s.label} data-reveal className="flex flex-col items-center gap-1.5 text-center">
                <span className="font-display text-3xl font-semibold sm:text-4xl"><CountUp value={s.value} className="text-gradient" /></span>
                <span className="text-xs text-muted-foreground">{s.label}</span>
              </div>
            ))}
          </Reveal>
        )}
      </div>
    </section>
  );
}

function ElectionsSection() {
  const q = usePublicOverview();
  const { user } = useAuth();
  return (
    <section id="elections" className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
      <div className="mb-8 space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Elections</p>
        <h2 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">What is on the ballot</h2>
      </div>
      {q.isPending ? (
        <div className="grid gap-4 md:grid-cols-2" role="status" aria-label="Loading elections">
          {[0, 1].map((i) => <div key={i} className="glass space-y-3 rounded-2xl p-5"><Skeleton className="h-5 w-2/3" /><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-1/2" /></div>)}
        </div>
      ) : q.isError ? (
        <ErrorState error={q.error} title="Could not load elections" hint="Start the backend with run.bat, then try again." onRetry={() => q.refetch()} />
      ) : q.data.elections.length === 0 ? (
        <EmptyState
          icon={<Vote />}
          title="No elections yet"
          description="An administrator creates elections and adds candidates. Sign in as admin to set one up."
          action={<Button asChild><Link to={user ? HOME_BY_ROLE[user.role] : "/login"}>{user ? "Open dashboard" : "Sign in as admin"}</Link></Button>}
        />
      ) : (
        <Reveal className="grid gap-4 md:grid-cols-2">
          {q.data.elections.map((e) => (
            <Card key={e.id} data-reveal className="space-y-3 p-5">
              <div className="flex items-start justify-between gap-3">
                <h3 className="font-display text-lg font-semibold leading-tight">{e.title}</h3>
                <StatusBadge status={e.status} />
              </div>
              {e.description && <p className="text-sm text-muted-foreground">{e.description}</p>}
              <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <CalendarClock className="size-3.5" /> {formatDate(e.start_time, true)} to {formatDate(e.end_time, true)}
              </p>
            </Card>
          ))}
        </Reveal>
      )}
    </section>
  );
}

export default function Landing() {
  const { user } = useAuth();
  const cta = user ? { to: HOME_BY_ROLE[user.role], label: "Go to dashboard", icon: <LayoutDashboard /> } : { to: "/login", label: "Enter AegisBallot", icon: <ArrowRight /> };
  return (
    <>
      <SmoothScroll />
      <AuroraBackground />
      <a href="#main" className="sr-only z-[90] rounded-lg bg-popover px-3 py-2 focus:not-sr-only focus:fixed focus:left-3 focus:top-3">Skip to content</a>
      <header className="sticky top-0 z-30 px-3 pt-3">
        <div className="glass mx-auto flex h-14 max-w-6xl items-center gap-2 rounded-2xl px-3 sm:px-4">
          <Link to="/" aria-label="AegisBallot home"><Logo /></Link>
          <nav aria-label="Sections" className="ml-6 hidden items-center gap-1 md:flex">
            <a href="#how-it-works" className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground">How it works</a>
            <a href="#elections" className="rounded-lg px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground">Elections</a>
          </nav>
          <div className="ml-auto flex items-center gap-1">
            <ThemeToggle />
            <Button asChild size="sm" magnetic={false}><Link to={cta.to}>{user ? "Dashboard" : "Sign in"}</Link></Button>
          </div>
        </div>
      </header>

      <main id="main" className="overflow-x-clip">
        <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-20 pt-14 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:pt-24">
          <SlideUp className="space-y-6">
            <Badge tone="violet" className="px-3 py-1 text-xs"><Fingerprint /> Demo verification environment · synthetic identities only</Badge>
            <h1 className="font-display text-4xl font-semibold leading-[1.05] tracking-tight text-balance sm:text-5xl lg:text-6xl">
              Secure, verifiable, <span className="text-gradient">private voting</span>
            </h1>
            <p className="max-w-xl text-lg text-muted-foreground">
              AegisBallot walks a voter from Aadhaar-style identity check to an encrypted ballot on a quorum-validated ledger, and lets an independent auditor prove nothing was altered.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <MagneticButton strength={0.3}>
                <Button asChild size="lg" magnetic={false}><Link to={cta.to}>{cta.label}{cta.icon}</Link></Button>
              </MagneticButton>
              <Button asChild size="lg" variant="secondary" magnetic={false}><a href="#how-it-works">See how it works</a></Button>
            </div>
          </SlideUp>
          <LedgerVisual />
        </section>

        <div className="py-6"><Marquee speed={45}>{PRIMITIVES.map((p) => <span key={p} className="glass rounded-full px-4 py-2 text-sm text-muted-foreground">{p}</span>)}</Marquee></div>

        <div className="py-14"><StatsStrip /></div>

        <section className="mx-auto max-w-6xl px-4 pb-6 sm:px-6">
          <Reveal className="grid gap-4 md:grid-cols-3">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <Card key={title} data-reveal interactive className="space-y-3 p-6">
                <span className="grid size-11 place-items-center rounded-2xl bg-grad-primary text-white shadow-[0_12px_30px_-10px_rgba(124,92,255,0.9)]"><Icon className="size-5" /></span>
                <h3 className="font-display text-lg font-semibold">{title}</h3>
                <p className="text-sm text-muted-foreground">{text}</p>
              </Card>
            ))}
          </Reveal>
        </section>

        <HowItWorks />
        <ElectionsSection />
      </main>

      <footer className="border-t border-[var(--glass-border)] px-4 py-8 text-center text-xs text-muted-foreground">
        <Logo className="mb-2" compact />
        <p>AegisBallot is a local demonstration. It does not contact UIDAI and is not a production election system.</p>
      </footer>
    </>
  );
}
