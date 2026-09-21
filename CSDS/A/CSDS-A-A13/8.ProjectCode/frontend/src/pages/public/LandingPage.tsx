import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <div className="flex min-h-dvh flex-col">
      <header className="container flex h-16 items-center justify-between">
        <Logo />
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button asChild variant="ghost">
            <Link to="/login">Sign in</Link>
          </Button>
        </div>
      </header>
      <main className="container flex flex-1 flex-col items-center justify-center py-16 text-center">
        <h1 className="max-w-3xl font-display text-4xl font-semibold text-balance sm:text-6xl">
          Fair, cheat-resistant exam seating in seconds.
        </h1>
        <p className="mt-5 max-w-xl text-muted-foreground">
          SeatWise turns your candidate list, halls and timetable into seating plans where no two neighbours write the same paper.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Button asChild size="lg">
            <Link to="/login">
              Get started <ArrowRight />
            </Link>
          </Button>
        </div>
      </main>
    </div>
  );
}
