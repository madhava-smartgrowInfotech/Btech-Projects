import { AnimatePresence, motion, useIsPresent } from "framer-motion";
import {
  Activity,
  BookOpenText,
  History as HistoryIcon,
  Languages,
  LayoutDashboard,
  LogIn,
  LogOut,
  Menu as MenuIcon,
  PanelLeftClose,
  PanelLeftOpen,
  ScanSearch,
  BarChart3,
  UserRound,
} from "lucide-react";
import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate, useOutlet } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { PageTransition } from "@/components/motion/PageTransition";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Avatar } from "@/components/ui/Avatar";
import { Button, IconButton } from "@/components/ui/Button";
import { Breadcrumbs } from "@/components/ui/Navigation";
import { Drawer } from "@/components/ui/Overlay";
import { Menu, Tooltip } from "@/components/ui/Popups";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { api, type User } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { LANGS, useLang, type Lang } from "@/lib/i18n";
import { useHealth } from "@/lib/queries";
import { cn } from "@/lib/utils";

interface NavItem {
  to: string;
  key: string;
  label: string;
  short: string;
  icon: typeof LayoutDashboard;
  auth: boolean;
}

export const NAV: NavItem[] = [
  { to: "/dashboard", key: "nav.dashboard", label: "Dashboard", short: "Home", icon: LayoutDashboard, auth: true },
  { to: "/detect", key: "nav.detect", label: "Detect", short: "Detect", icon: ScanSearch, auth: true },
  { to: "/history", key: "nav.history", label: "History", short: "History", icon: HistoryIcon, auth: true },
  { to: "/analytics", key: "nav.analytics", label: "Analytics", short: "Charts", icon: BarChart3, auth: true },
  { to: "/encyclopedia", key: "nav.guide", label: "Disease guide", short: "Guide", icon: BookOpenText, auth: false },
  { to: "/profile", key: "nav.profile", label: "Profile", short: "Profile", icon: UserRound, auth: true },
];

/* ---- breadcrumb label for detail pages (e.g. the disease name) ---- */
const CrumbContext = createContext<(label: string | null) => void>(() => undefined);

/** Detail pages call this to show their own name as the last breadcrumb. */
export function useBreadcrumb(label: string | null | undefined) {
  const set = useContext(CrumbContext);
  useEffect(() => {
    set(label ?? null);
    return () => set(null);
  }, [label, set]);
}

const COLLAPSE_KEY = "agrivision-sidebar-collapsed";

function useNav() {
  const { user } = useAuth();
  const { t } = useLang();
  return NAV.filter((n) => !n.auth || user).map((n) => ({ ...n, text: t(n.key, n.label) }));
}

/** The product's honest status line: which engine produced the diagnoses. */
function EngineNote() {
  const health = useHealth();
  const h = health.data;
  return (
    <div className="relative overflow-hidden rounded-2xl border border-[var(--glass-border)] bg-grad-soft p-3 text-xs text-muted-foreground">
      {h ? (
        h.trained_model ? (
          <>Diagnosing with the trained model <b className="text-foreground">{h.engine}</b>.</>
        ) : (
          <>
            Engine: <b className="text-foreground">colour/texture heuristic</b>. No trained CNN is installed, so treat results as a first screen and confirm with your agri officer.
          </>
        )
      ) : (
        "Checking the diagnosis engine…"
      )}
    </div>
  );
}

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
          <Link to="/" aria-label="AgriVision home">
            <Logo compact={collapsed} />
          </Link>
        </div>
        <NavLinks collapsed={collapsed} />
        <div className="mt-auto space-y-3">
          {!collapsed && <EngineNote />}
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
  const items = useNav();
  return (
    <nav className="flex flex-col gap-1" aria-label="Main">
      {items.map(({ to, text, icon: Icon }) => {
        const link = (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            aria-label={collapsed ? text : undefined}
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
                    className="absolute inset-0 rounded-xl border border-[color-mix(in_srgb,var(--violet)_35%,transparent)] bg-grad-soft shadow-[0_0_20px_-6px_rgba(34,160,107,0.6)]"
                    transition={{ type: "spring", stiffness: 500, damping: 40 }}
                  />
                )}
                <Icon className={cn("relative size-[18px] shrink-0", isActive && "text-violet-ink")} />
                {!collapsed && <span className="relative truncate">{text}</span>}
              </>
            )}
          </NavLink>
        );
        return collapsed ? (
          <Tooltip key={to} content={text} side="right">
            {link}
          </Tooltip>
        ) : (
          link
        );
      })}
    </nav>
  );
}

/** Live API status: green when the API answers, red with a hint when it does not. */
function ApiStatus() {
  const health = useHealth();
  const ok = health.isSuccess;
  const pending = health.isPending;
  return (
    <span
      role="status"
      className={cn(
        "hidden items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium md:inline-flex",
        ok ? "border-success/30 bg-success/12 text-success" : pending ? "border-[var(--glass-border)] text-muted-foreground" : "border-danger/30 bg-danger/12 text-danger",
      )}
    >
      <Activity className="size-3.5" aria-hidden />
      {ok ? "API online" : pending ? "Connecting…" : "API offline - start run.bat"}
    </span>
  );
}

/** EN / HI / MR switch. A signed-in user's choice is also saved to their profile. */
export function LanguageMenu() {
  const { lang, setLang, t } = useLang();
  const { user, setUser } = useAuth();

  function choose(next: Lang) {
    setLang(next);
    if (user) {
      api
        .put<User>("/v1/profile", { full_name: user.full_name, region: user.region, language: next, crops: user.crops })
        .then((r) => setUser(r.data))
        .catch(() => undefined);
    }
  }

  return (
    <Menu
      trigger={
        <button
          type="button"
          className="flex h-10 items-center gap-1.5 rounded-xl px-2.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          aria-label={`${t("common.language", "Language")}: ${LANGS.find((l) => l.value === lang)?.label}`}
        >
          <Languages className="size-4" aria-hidden />
          <span className="hidden sm:inline">{LANGS.find((l) => l.value === lang)?.label}</span>
        </button>
      }
      items={LANGS.map((l) => ({ label: l.label, active: l.value === lang, onSelect: () => choose(l.value) }))}
    />
  );
}

function UserMenu() {
  const { user, logout } = useAuth();
  const { t } = useLang();
  const navigate = useNavigate();
  if (!user) {
    return (
      <Button asChild size="sm">
        <Link to="/login">
          <LogIn /> {t("common.signin", "Sign in")}
        </Link>
      </Button>
    );
  }
  return (
    <Menu
      trigger={
        <button type="button" className="flex h-10 items-center gap-2 rounded-xl px-1.5 transition-colors hover:bg-muted" aria-label="Account menu">
          <Avatar name={user.full_name || user.email} />
          <span className="hidden max-w-[140px] truncate text-sm font-medium md:inline">{user.full_name || user.email}</span>
        </button>
      }
      header={
        <>
          <div className="truncate text-sm font-medium">{user.full_name || "My account"}</div>
          <div className="truncate text-xs text-muted-foreground">{user.email}</div>
        </>
      }
      items={[
        { label: t("nav.profile", "Profile"), icon: <UserRound />, onSelect: () => navigate("/profile") },
        {
          label: t("common.signout", "Sign out"),
          icon: <LogOut />,
          onSelect: () => {
            logout();
            navigate("/");
          },
        },
      ]}
    />
  );
}

export function Topbar({ onOpenMenu, crumb }: { onOpenMenu: () => void; crumb: string | null }) {
  const location = useLocation();
  const { t } = useLang();
  const items = useMemo(() => {
    const parts = location.pathname.split("/").filter(Boolean);
    const section = NAV.find((n) => n.to === `/${parts[0] ?? ""}`) ?? (parts[0] === "result" ? NAV[2] : parts[0] === "disease" ? NAV[4] : NAV[0]);
    const list: { label: string; to?: string }[] = [{ label: "AgriVision", to: "/" }, { label: t(section.key, section.label), to: section.to }];
    if (parts.length > 1) list.push({ label: crumb ?? "Details" });
    return list;
  }, [location.pathname, crumb, t]);

  return (
    <header className="sticky top-0 z-20 px-3 pt-3 lg:pl-0">
      <div className="glass flex h-14 items-center gap-2 rounded-2xl px-2 sm:px-3">
        <IconButton label="Open menu" className="lg:hidden" onClick={onOpenMenu}>
          <MenuIcon />
        </IconButton>
        <Link to="/" className="shrink-0 lg:hidden" aria-label="AgriVision home">
          <Logo compact />
        </Link>
        <Breadcrumbs items={items} className="ml-1 hidden sm:block" />
        <div className="ml-auto flex items-center gap-1">
          <ApiStatus />
          <LanguageMenu />
          <ThemeToggle />
          <UserMenu />
        </div>
      </div>
    </header>
  );
}

function BottomBar() {
  const items = useNav().slice(0, 5);
  return (
    <nav aria-label="Quick navigation" className="fixed inset-x-0 bottom-0 z-30 px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] lg:hidden">
      <div className="glass-strong mx-auto flex max-w-md items-center justify-around rounded-2xl px-1 py-1.5">
        {items.map(({ to, short, icon: Icon }) => (
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
  const routeKey = location.pathname.split("/").slice(0, 2).join("/");
  const { user } = useAuth();
  const { setLang } = useLang();
  const synced = useRef<string | null>(null);

  // a signed-in user's saved language wins once per sign-in
  useEffect(() => {
    if (user && synced.current !== user.id) {
      synced.current = user.id;
      setLang(user.language);
    }
  }, [user, setLang]);

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
          <div className="mt-6">
            <EngineNote />
          </div>
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
