import { AnimatePresence, motion, useIsPresent } from "framer-motion";
import {
  Activity,
  Camera,
  Hand,
  Info,
  LayoutDashboard,
  Menu as MenuIcon,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Sun,
  Dumbbell,
} from "lucide-react";
import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import { Link, NavLink, useLocation, useOutlet } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { PageTransition } from "@/components/motion/PageTransition";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Button, IconButton } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Breadcrumbs } from "@/components/ui/Navigation";
import { Drawer } from "@/components/ui/Overlay";
import { Tooltip } from "@/components/ui/Popups";
import { useHealth } from "@/lib/queries";
import { useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";

export const NAV = [
  { to: "/app", label: "Dashboard", short: "Home", icon: LayoutDashboard, end: true },
  { to: "/app/recognize", label: "Recognize", short: "Recognize", icon: Hand },
  { to: "/app/collect", label: "Collect data", short: "Collect", icon: Camera },
  { to: "/app/train", label: "Train model", short: "Train", icon: Dumbbell },
  { to: "/app/model", label: "Model performance", short: "Model", icon: Activity },
  { to: "/app/about", label: "About", short: "About", icon: Info },
];

/* ---- breadcrumb label for detail pages (e.g. the policy's name) ---- */
const CrumbContext = createContext<(label: string | null) => void>(() => undefined);

/** Detail pages call this to show their own name as the last breadcrumb. */
export function useBreadcrumb(label: string | null | undefined) {
  const set = useContext(CrumbContext);
  useEffect(() => {
    set(label ?? null);
    return () => set(null);
  }, [label, set]);
}

const COLLAPSE_KEY = "signspeak-sidebar-collapsed";

export function Sidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  return (
    <aside
      className={cn(
        "sticky top-0 z-30 hidden h-dvh shrink-0 flex-col p-3 transition-[width] duration-300 lg:flex",
        collapsed ? "w-[84px]" : "w-64",
      )}
    >
      <div className="glass flex h-full flex-col rounded-3xl px-3 py-4">
        <div className={cn("mb-6 flex items-center", collapsed ? "justify-center" : "justify-between px-1.5")}>
          <Link to="/app" aria-label="SignSpeak dashboard">
            <Logo compact={collapsed} />
          </Link>
        </div>
        <NavLinks collapsed={collapsed} />
        <div className="mt-auto space-y-3">
          {!collapsed && (
            <div className="relative overflow-hidden rounded-2xl border border-[var(--glass-border)] bg-grad-soft p-3 text-xs text-muted-foreground">
              Hold a sign steady for about a second and the letter is typed into your sentence.
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            magnetic={false}
            onClick={onToggle}
            className={cn("w-full", collapsed ? "justify-center px-0" : "justify-start")}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <PanelLeftOpen /> : <PanelLeftClose />}
            {!collapsed && "Collapse"}
          </Button>
        </div>
      </div>
    </aside>
  );
}

function NavLinks({ collapsed = false, onNavigate }: { collapsed?: boolean; onNavigate?: () => void }) {
  return (
    <nav className="flex flex-col gap-1" aria-label="Main">
      {NAV.map(({ to, label, icon: Icon, end }) => {
        const link = (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            aria-label={collapsed ? label : undefined}
            className={({ isActive }) =>
              cn(
                "group relative flex h-10 items-center gap-3 rounded-xl px-3 text-sm font-medium transition-colors",
                collapsed && "justify-center px-0",
                isActive ? "text-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <motion.span
                    layoutId={onNavigate ? "nav-active-drawer" : "nav-active"}
                    className="absolute inset-0 rounded-xl border border-[color-mix(in_srgb,var(--violet)_35%,transparent)] bg-grad-soft shadow-[0_0_20px_-6px_rgba(124,92,255,0.6)]"
                    transition={{ type: "spring", stiffness: 500, damping: 40 }}
                  />
                )}
                <Icon className={cn("relative size-[18px] shrink-0", isActive && "text-violet-ink")} />
                {!collapsed && <span className="relative truncate">{label}</span>}
              </>
            )}
          </NavLink>
        );
        return collapsed ? (
          <Tooltip key={to} content={label} side="right">
            {link}
          </Tooltip>
        ) : (
          link
        );
      })}
    </nav>
  );
}

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const dark = resolvedTheme === "dark";
  return (
    <IconButton
      label={dark ? "Switch to light mode" : "Switch to dark mode"}
      onClick={() => {
        setTheme(dark ? "light" : "dark");
      }}
    >
      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={dark ? "moon" : "sun"}
          initial={{ rotate: -90, opacity: 0, scale: 0.6 }}
          animate={{ rotate: 0, opacity: 1, scale: 1 }}
          exit={{ rotate: 90, opacity: 0, scale: 0.6 }}
          transition={{ duration: 0.2 }}
          className="grid place-items-center"
        >
          {dark ? <Moon /> : <Sun />}
        </motion.span>
      </AnimatePresence>
    </IconButton>
  );
}

function ModelStatus() {
  const { data, isError } = useHealth();
  if (isError) return <Badge tone="danger">API offline</Badge>;
  if (!data) return null;
  if (data.training_state === "training" || data.training_state === "loading") return <Badge tone="warning">Training…</Badge>;
  return data.model_loaded ? <Badge tone="success">Model ready</Badge> : <Badge tone="neutral">No model yet</Badge>;
}

export function Topbar({ onOpenMenu, crumb }: { onOpenMenu: () => void; crumb: string | null }) {
  const location = useLocation();
  const items = useMemo(() => {
    const parts = location.pathname.split("/").filter(Boolean); // ["app", "policies", "4"]
    const section = NAV.find((n) => n.to === `/${parts.slice(0, 2).join("/")}`) ?? NAV[0];
    const list: { label: string; to?: string }[] = [{ label: "SignSpeak", to: "/app" }];
    if (section.to !== "/app") list.push({ label: section.label, to: section.to });
    else list.push({ label: "Dashboard", to: "/app" });
    if (parts.length > 2) list.push({ label: crumb ?? "Details" });
    return list;
  }, [location.pathname, crumb]);

  return (
    <header className="sticky top-0 z-20 px-3 pt-3 lg:pl-0">
      <div className="glass flex h-14 items-center gap-2 rounded-2xl px-2 sm:px-3">
        <IconButton label="Open menu" className="lg:hidden" onClick={onOpenMenu}>
          <MenuIcon />
        </IconButton>
        <Link to="/app" className="shrink-0 lg:hidden" aria-label="SignSpeak dashboard">
          <Logo compact />
        </Link>
        <Breadcrumbs items={items} className="ml-1 hidden sm:block" />
        <div className="ml-auto flex items-center gap-1">
          <span className="hidden sm:inline-flex"><ModelStatus /></span>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}

function BottomBar() {
  const items = NAV.slice(0, 5);
  return (
    <nav aria-label="Quick navigation" className="fixed inset-x-0 bottom-0 z-30 px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] lg:hidden">
      <div className="glass-strong mx-auto flex max-w-md items-center justify-around rounded-2xl px-1 py-1.5">
        {items.map(({ to, short, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "relative flex min-w-0 flex-1 flex-col items-center gap-0.5 rounded-xl py-1.5 text-[10px] font-medium transition-colors",
                isActive ? "text-foreground" : "text-muted-foreground",
              )
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <motion.span layoutId="bottom-active" className="absolute inset-0 rounded-xl bg-grad-soft" transition={{ type: "spring", stiffness: 500, damping: 40 }} />
                )}
                <Icon className={cn("relative size-5", isActive && "text-violet-ink")} />
                <span className="relative truncate">{short}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}

/** Keeps rendering the outgoing route while its exit animation plays (an <Outlet> would already show the new route). */
function FrozenOutlet() {
  const outlet = useOutlet();
  const present = useIsPresent();
  const last = useRef(outlet);
  if (present) last.current = outlet;
  return last.current;
}

export function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [crumb, setCrumb] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem(COLLAPSE_KEY) === "1";
    } catch {
      return false;
    }
  });
  const location = useLocation();
  const routeKey = location.pathname.split("/").slice(0, 3).join("/");

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [routeKey]);

  return (
    <CrumbContext.Provider value={setCrumb}>
      <AuroraBackground intensity={0.9} />
      <a href="#main" className="sr-only z-[90] rounded-lg bg-popover px-3 py-2 focus:not-sr-only focus:fixed focus:left-3 focus:top-3">
        Skip to content
      </a>
      <div className="flex min-h-dvh">
        <Sidebar
          collapsed={collapsed}
          onToggle={() =>
            setCollapsed((v) => {
              try {
                localStorage.setItem(COLLAPSE_KEY, v ? "0" : "1");
              } catch {
                /* ignore */
              }
              return !v;
            })
          }
        />
        <Drawer open={menuOpen} onOpenChange={setMenuOpen} side="left" title={<Logo />} description="Main navigation" className="w-72">
          <NavLinks onNavigate={() => setMenuOpen(false)} />
        </Drawer>
        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar onOpenMenu={() => setMenuOpen(true)} crumb={crumb} />
          <main id="main" className="mx-auto w-full max-w-7xl flex-1 px-3 pb-28 pt-6 sm:px-6 lg:px-8 lg:pb-10">
            <AnimatePresence mode="wait" initial={false}>
              <PageTransition key={routeKey}>
                <FrozenOutlet />
              </PageTransition>
            </AnimatePresence>
          </main>
        </div>
      </div>
      <BottomBar />
    </CrumbContext.Provider>
  );
}
