import { Link, NavLink, Outlet, useNavigate } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/lib/auth";
import { ThemeToggle } from "./ThemeToggle.jsx";

const linkClass = ({ isActive }) =>
  `rounded-xl px-3 py-2 text-sm font-medium transition-colors ${
    isActive ? "text-foreground" : "text-muted-foreground hover:text-foreground"
  }`;

/** Header and aurora backdrop for the pages that do not need a login: landing, auth and evaluation. */
export function PublicShell() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  return (
    <>
      <AuroraBackground intensity={0.9} />
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[90] focus:rounded-lg focus:bg-popover focus:px-3 focus:py-2">
        Skip to content
      </a>
      <header className="sticky top-0 z-20 px-3 pt-3 sm:px-6">
        <div className="glass mx-auto flex h-14 max-w-6xl items-center gap-2 rounded-2xl px-3">
          <Link to="/" aria-label="ClauseGuard home" className="shrink-0">
            <Logo />
          </Link>
          <nav aria-label="Main" className="ml-auto flex items-center gap-1 sm:gap-2">
            <NavLink to="/evaluation" className={`${linkClass} hidden sm:inline-flex`}>
              Evaluation
            </NavLink>
            {isAuthenticated ? (
              <Button size="sm" onClick={() => navigate("/app")}>
                Open app
              </Button>
            ) : (
              <>
                <NavLink to="/login" className={linkClass}>
                  Log in
                </NavLink>
                <Button asChild size="sm">
                  <Link to="/register">Sign up</Link>
                </Button>
              </>
            )}
            <ThemeToggle />
          </nav>
        </div>
      </header>
      <main id="main" className="mx-auto w-full max-w-6xl px-4 pb-16 pt-8 sm:px-6">
        <Outlet />
      </main>
    </>
  );
}
