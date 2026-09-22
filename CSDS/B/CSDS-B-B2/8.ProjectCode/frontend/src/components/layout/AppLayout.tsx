import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { Menu, WifiOff } from "lucide-react";
import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet";
import { hasRole } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { NAV } from "./nav";
import { ThemeToggle } from "./ThemeToggle";
import { UserMenu } from "./UserMenu";

function useOnline() {
  const [online, setOnline] = useState(() => navigator.onLine);
  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);
  return online;
}

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const { user } = useAuth();
  return (
    <nav aria-label="Main" className="flex flex-col gap-6 px-3 py-4">
      {NAV.map((section) => {
        const items = section.items.filter((i) => hasRole(user, i.minRole));
        if (!items.length) return null;
        return (
          <div key={section.title}>
            <p className="mb-1.5 px-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{section.title}</p>
            <ul className="flex flex-col gap-0.5">
              {items.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.end}
                    onClick={onNavigate}
                    className={({ isActive }) =>
                      cn(
                        "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                        isActive ? "bg-primary/10 text-primary" : "text-sidebar-foreground/80 hover:bg-accent hover:text-accent-foreground",
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && <motion.span layoutId="nav-active" className="absolute inset-y-1.5 left-0 w-1 rounded-r-full bg-primary" transition={{ type: "spring", stiffness: 500, damping: 40 }} />}
                        <item.icon className="h-[18px] w-[18px] shrink-0" aria-hidden />
                        {item.label}
                      </>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </nav>
  );
}

export function AppLayout() {
  const [open, setOpen] = useState(false);
  const online = useOnline();
  const location = useLocation();

  return (
    <div className="flex min-h-dvh">
      <aside className="sticky top-0 hidden h-dvh w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar lg:flex">
        <Link to="/app" className="flex h-16 items-center border-b border-sidebar-border px-5" aria-label="SignalScout home">
          <Logo />
        </Link>
        <div className="flex-1 overflow-y-auto">
          <SidebarNav />
        </div>
        <p className="border-t border-sidebar-border px-5 py-3 text-xs text-muted-foreground">SignalScout v1.0</p>
      </aside>

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent side="left" className="p-0">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <SheetDescription className="sr-only">Pages of SignalScout</SheetDescription>
          <div className="flex h-16 items-center border-b border-sidebar-border px-5">
            <Logo />
          </div>
          <div className="flex-1 overflow-y-auto">
            <SidebarNav onNavigate={() => setOpen(false)} />
          </div>
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center gap-2 border-b bg-background/85 px-3 backdrop-blur-md sm:px-6">
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu">
            <Menu />
          </Button>
          <Link to="/app" className="lg:hidden" aria-label="SignalScout home">
            <Logo compact />
          </Link>
          <div className="flex-1" />
          <ThemeToggle />
          <UserMenu />
        </header>

        <AnimatePresence>
          {!online && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden border-b border-zone-weak/40 bg-zone-weak/15"
              role="status"
            >
              <p className="flex items-center gap-2 px-4 py-2 text-sm sm:px-6">
                <WifiOff className="h-4 w-4 shrink-0" aria-hidden /> You are offline. Showing the last data you loaded; changes will sync when the connection returns.
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <motion.div key={location.pathname} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22, ease: "easeOut" }} className="mx-auto w-full max-w-7xl">
            <Outlet />
          </motion.div>
        </main>
      </div>
    </div>
  );
}
