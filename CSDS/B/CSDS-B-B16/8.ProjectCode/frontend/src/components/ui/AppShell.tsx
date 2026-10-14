import { AnimatePresence, motion, useIsPresent } from "framer-motion";
import { Activity, BarChart3, LogOut, Menu as MenuIcon, PanelLeftClose, PanelLeftOpen, ScanEye, Users } from "lucide-react";
import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate, useOutlet } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/app/ThemeToggle";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { PageTransition } from "@/components/motion/PageTransition";
import { Avatar } from "@/components/ui/Avatar";
import { Button, IconButton } from "@/components/ui/Button";
import { Breadcrumbs } from "@/components/ui/Navigation";
import { Drawer } from "@/components/ui/Overlay";
import { Menu, Tooltip } from "@/components/ui/Popups";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

export const NAV = [
  { to: "/screening/new", label: "New screening", short: "New", icon: ScanEye },
  { to: "/patients", label: "Patients & history", short: "Patients", icon: Users },
  { to: "/performance", label: "Model performance", short: "Performance", icon: BarChart3 },
];

/* ---- breadcrumb label for detail pages (e.g. "Screening #12") ---- */
const CrumbContext = createContext<(label: string | null) => void>(() => undefined);

/** Detail pages call this to show their own name as the last breadcrumb. */
export function useBreadcrumb(label: string | null | undefined) {
  const set = useContext(CrumbContext);
  useEffect(() => {
    set(label ?? null);
    return () => set(null);
  }, [label, set]);
}

const COLLAPSE_KEY = "retinaguard-sidebar-collapsed";

function Sidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  return (
    <aside
      className={cn(
        "sticky top-0 z-30 hidden h-dvh shrink-0 flex-col p-3 transition-[width] duration-300 lg:flex",
        collapsed ? "w-[84px]" : "w-64",
      )}
    >
      <div className="glass flex h-full flex-col rounded-3xl px-3 py-4">
        <div className={cn("mb-6 flex items-center", collapsed ? "justify-center" : "justify-between px-1.5")}>
          <Link to="/screening/new" aria-label="RetinaGuard home">
            <Logo compact={collapsed} />
          </Link>
        </div>
        <NavLinks collapsed={collapsed} />
        <div className="mt-auto space-y-3">
          {!collapsed && (
            <div className="relative overflow-hidden rounded-2xl border border-[var(--glass-border)] bg-grad-soft p-3 text-xs text-muted-foreground">
              Decision support only. Every result is reviewed by a qualified professional.
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
      {NAV.map(({ to, label, icon: Icon }) => {
        const link = (
          <NavLink
            key={to}
            to={to}
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

function UserMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  if (!user) return null;
  return (
    <Menu
      trigger={
        <button type="button" className="flex h-10 items-center gap-2 rounded-xl px-1.5 transition-colors hover:bg-muted" aria-label="Account menu">
          <Avatar name={user.name} />
          <span className="hidden max-w-[140px] truncate text-sm font-medium md:inline">{user.name}</span>
        </button>
      }
      header={
        <>
          <div className="truncate text-sm font-medium">{user.name}</div>
          <div className="truncate text-xs capitalize text-muted-foreground">{user.role}</div>
        </>
      }
      items={[
        {
          label: "Sign out",
          icon: <LogOut />,
          danger: true,
          onSelect: () => {
            logout();
            navigate("/login");
          },
        },
      ]}
    />
  );
}

/** Which top-level section a path belongs to, for the breadcrumb trail. */
function sectionFor(pathname: string): { label: string; to: string } | null {
  if (pathname.startsWith("/screenings")) return { label: "Screenings", to: "/patients" };
  const hit = NAV.find((n) => pathname.startsWith(n.to));
  return hit ? { label: hit.label, to: hit.to } : null;
}

function Topbar({ onOpenMenu, crumb }: { onOpenMenu: () => void; crumb: string | null }) {
  const location = useLocation();
  const items = useMemo(() => {
    const list: { label: string; to?: string }[] = [{ label: "RetinaGuard", to: "/screening/new" }];
    const section = sectionFor(location.pathname);
    if (section) list.push(section);
    if (crumb) list.push({ label: crumb });
    return list;
  }, [location.pathname, crumb]);

  return (
    <header className="sticky top-0 z-20 px-3 pt-3 lg:pl-0">
      <div className="glass flex h-14 items-center gap-2 rounded-2xl px-2 sm:px-3">
        <IconButton label="Open menu" className="lg:hidden" onClick={onOpenMenu}>
          <MenuIcon />
        </IconButton>
        <Link to="/screening/new" className="shrink-0 lg:hidden" aria-label="RetinaGuard home">
          <Logo compact />
        </Link>
        <Breadcrumbs items={items} className="ml-1 hidden sm:block" />
        <div className="ml-auto flex items-center gap-1">
          <ThemeToggle />
          <UserMenu />
        </div>
      </div>
    </header>
  );
}

function BottomBar() {
  return (
    <nav aria-label="Quick navigation" className="fixed inset-x-0 bottom-0 z-30 px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] lg:hidden">
      <div className="glass-strong mx-auto flex max-w-md items-center justify-around rounded-2xl px-1 py-1.5">
        {NAV.map(({ to, short, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
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

/** Layout route for every signed-in screen: sidebar on desktop, drawer and bottom bar on phones. */
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
