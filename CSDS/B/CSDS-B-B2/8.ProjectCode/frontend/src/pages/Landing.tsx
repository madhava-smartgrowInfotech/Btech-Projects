import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowRight, BellRing, MapPinned, Navigation, Radar, ShieldCheck, WifiOff } from "lucide-react";
import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";

const FEATURES = [
  { icon: Radar, title: "Measured, not guessed", text: "Phones and sensor nodes record signal, speed and connectivity; every reading is classified Strong, Weak or Dead." },
  { icon: MapPinned, title: "Coverage you can see", text: "Heat and hexagon maps by operator and time of day show exactly where service fails." },
  { icon: Navigation, title: "Better signal, nearby", text: "A spatial model predicts the signal around you and points to the closest strong spot." },
  { icon: BellRing, title: "Complaints that file themselves", text: "Zones that stay bad become complaints with evidence, then get verified from new readings." },
  { icon: WifiOff, title: "Works offline", text: "Readings are stored on the device during outages and sync the moment the connection returns." },
  { icon: ShieldCheck, title: "Built for operator desks", text: "Engineers get a queue, the evidence and a clear lifecycle from detection to verified fix." },
];

export default function Landing() {
  const { user } = useAuth();
  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-30 border-b bg-background/80 backdrop-blur-md">
        <div className="container flex h-16 items-center justify-between">
          <Link to="/" aria-label="SignalScout home">
            <Logo compact className="sm:hidden" />
            <Logo className="hidden sm:inline-flex" />
          </Link>
          <div className="flex items-center gap-1 sm:gap-2">
            <ThemeToggle />
            {user ? (
              <Button asChild size="sm">
                <Link to="/app">Open dashboard</Link>
              </Button>
            ) : (
              <>
                <Button asChild variant="ghost" size="sm">
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

      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-grid [mask-image:radial-gradient(ellipse_at_top,black_30%,transparent_70%)]" aria-hidden />
        <div className="container relative py-20 text-center sm:py-28">
          <motion.p initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mx-auto mb-4 inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
            <span className="h-2 w-2 rounded-full bg-zone-strong" aria-hidden /> Live coverage intelligence for mobile networks
          </motion.p>
          <motion.h1 initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="mx-auto max-w-3xl text-balance text-4xl font-bold leading-[1.1] sm:text-6xl">
            Find dead zones. <span className="text-primary">Fix them faster.</span>
          </motion.h1>
          <motion.p initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mx-auto mt-5 max-w-2xl text-balance text-base text-muted-foreground sm:text-lg">
            SignalScout turns real phone and sensor readings into a live coverage map, guides people to better signal and files complaints with the technical evidence operators need.
          </motion.p>
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <Button asChild size="lg">
              <Link to={user ? "/app" : "/register"}>
                Get started <ArrowRight />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link to="/login">Try a demo account</Link>
            </Button>
          </motion.div>
        </div>
      </section>

      <section className="container pb-20">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ delay: i * 0.05 }}
              whileHover={{ y: -3 }}
              className="rounded-xl border bg-card p-6 shadow-sm"
            >
              <f.icon className="h-6 w-6 text-primary" aria-hidden />
              <h3 className="mt-4 text-lg font-semibold">{f.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{f.text}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <footer className="border-t">
        <div className="container flex flex-col items-center justify-between gap-3 py-6 text-sm text-muted-foreground sm:flex-row">
          <Logo className="scale-90" />
          <p>© {new Date().getFullYear()} SignalScout. Coverage data you can act on.</p>
        </div>
      </footer>
    </div>
  );
}
