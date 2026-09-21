import type { ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";
import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

export function PublicHeader({ transparent = false }: { transparent?: boolean }) {
  const { user } = useAuth();
  return (
    <header className={cn("sticky top-0 z-40 border-b backdrop-blur", transparent ? "border-transparent bg-background/60" : "bg-background/85")}>
      <div className="container flex h-16 items-center justify-between gap-3">
        <Link to="/" aria-label="SeatWise home">
          <Logo />
        </Link>
        <nav className="flex items-center gap-1 sm:gap-2" aria-label="Site">
          <NavLink
            to="/lookup"
            className={({ isActive }) =>
              cn("hidden rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground sm:block", isActive && "text-foreground")
            }
          >
            Find my seat
          </NavLink>
          <ThemeToggle />
          <Button asChild size="sm">
            <Link to={user ? "/app" : "/login"}>{user ? "Open SeatWise" : "Sign in"}</Link>
          </Button>
        </nav>
      </div>
    </header>
  );
}

export function PublicFooter() {
  return (
    <footer className="border-t">
      <div className="container flex flex-col gap-6 py-10 sm:flex-row sm:items-start sm:justify-between">
        <div className="max-w-sm">
          <Logo />
          <p className="mt-3 text-sm text-muted-foreground">
            Constraint-optimised, cheat-resistant exam seating plans, generated in seconds and reproducible from their seed.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-10 text-sm">
          <div className="space-y-2">
            <div className="font-semibold">Candidates</div>
            <Link to="/lookup" className="block text-muted-foreground hover:text-foreground">Find my seat</Link>
          </div>
          <div className="space-y-2">
            <div className="font-semibold">Staff</div>
            <Link to="/login" className="block text-muted-foreground hover:text-foreground">Sign in</Link>
            <Link to="/register" className="block text-muted-foreground hover:text-foreground">Request an account</Link>
          </div>
        </div>
      </div>
      <div className="container border-t py-5 text-xs text-muted-foreground">© {new Date().getFullYear()} SeatWise. All rights reserved.</div>
    </footer>
  );
}

export function PublicShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col">
      <PublicHeader />
      <main className="flex-1">{children}</main>
      <PublicFooter />
    </div>
  );
}
