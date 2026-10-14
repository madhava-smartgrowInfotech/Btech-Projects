import { AnimatePresence, motion, useIsPresent } from "framer-motion";
import {
  Building2,
  LogOut,
  Menu as MenuIcon,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  ScrollText,
  Stethoscope,
  Sun,
  UserRound,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate, useOutlet } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { PageTransition } from "@/components/motion/PageTransition";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Avatar } from "@/components/ui/Avatar";
import { Button, IconButton } from "@/components/ui/Button";
import { Breadcrumbs } from "@/components/ui/Navigation";
import { Drawer } from "@/components/ui/Overlay";
import { Menu, Tooltip } from "@/components/ui/Popups";
import { HOME, type Role, useAuth } from "@/lib/auth";
import { ROLE_LABEL } from "@/lib/constants";
import { useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";

export interface NavItem {
  to: string;
  label: string;
  short: string;
  icon: LucideIcon;
  roles: Role[];
}

/** Screens per role. The sidebar and bottom bar show only the ones the signed-in role may open. */
export const NAV: NavItem[] = [
  { to: "/patient", label: "My health record", short: "Record", icon: UserRound, roles: ["patient"] },
  { to: "/doctor", label: "Patient lookup", short: "Lookup", icon: Stethoscope, roles: ["doctor"] },
  { to: "/hospital", label: "Hospital console", short: "Hospital", icon: Building2, roles: ["staff", "admin"] },
  { to: "/audit", label: "Audit & consent log", short: "Audit", icon: ScrollText, roles: ["patient", "doctor", "staff", "admin"] },
];

export function navFor(role: Role | undefined): NavItem[] {
  return role ? NAV.filter((n) => n.roles.includes(role)) : [];
}

const COLLAPSE_KEY = "unihealth-sidebar-collapsed";

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
          <Link to="/" aria-label="UniHealth home">
            <Logo compact={collapsed} />
          </Link>
        </div>
        <NavLinks collapsed={collapsed} />
        <div className="mt-auto space-y-3">
          {!collapsed && (
            <div className="relative overflow-hidden rounded-2xl border border-[var(--glass-border)] bg-grad-soft p-3 text-xs text-muted-foreground">
              Every access to a record is checked against the patient's consent and written to the audit ledger.
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
  const { user } = useAuth();
  return (
    <nav className="flex flex-col gap-1" aria-label="Main">
      {navFor(user?.role).map(({ to, label, icon: Icon }) => {
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

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const dark = resolvedTheme === "dark";
  return (
    <IconButton label={dark ? "Switch to light mode" : "Switch to dark mode"} onClick={() => setTheme(dark ? "light" : "dark")}>
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

function UserMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  if (!user) return null;
  return (
    <Menu
      trigger={
        <button type="button" className="flex h-10 items-center gap-2 rounded-xl px-1.5 transition-colors hover:bg-muted" aria-label="Account menu">
          <Avatar name={user.display_name} />
          <span className="hidden max-w-[160px] truncate text-sm font-medium md:inline">{user.display_name}</span>
        </button>
      }
      header={
        <>
          <div className="truncate text-sm font-medium">{user.display_name}</div>
          <div className="truncate text-xs text-muted-foreground">
            {ROLE_LABEL[user.role]}
            {user.hospital_name ? ` - ${user.hospital_name}` : ""}
          </div>
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

export function Topbar({ onOpenMenu }: { onOpenMenu: () => void }) {
  const location = useLocation();
  const { user } = useAuth();
  const items = useMemo(() => {
    const home = user ? HOME[user.role] : "/";
    const section = navFor(user?.role).find((n) => location.pathname.startsWith(n.to));
    const list: { label: string; to?: string }[] = [{ label: "UniHealth", to: home }];
    if (section) list.push({ label: section.label });
    return list;
  }, [location.pathname, user]);

  return (
    <header className="sticky top-0 z-20 px-3 pt-3 lg:pl-0">
      <div className="glass flex h-14 items-center gap-2 rounded-2xl px-2 sm:px-3">
        <IconButton label="Open menu" className="lg:hidden" onClick={onOpenMenu}>
          <MenuIcon />
        </IconButton>
        <Link to={user ? HOME[user.role] : "/"} className="shrink-0 lg:hidden" aria-label="UniHealth home">
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
  const { user } = useAuth();
  const items = navFor(user?.role).slice(0, 5);
  if (items.length === 0) return null;
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
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return window.localStorage.getItem(COLLAPSE_KEY) === "1";
    } catch {
      return false;
    }
  });
  const location = useLocation();
  const routeKey = `/${location.pathname.split("/")[1] ?? ""}`;

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [routeKey]);

  return (
    <>
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
                window.localStorage.setItem(COLLAPSE_KEY, v ? "0" : "1");
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
          <Topbar onOpenMenu={() => setMenuOpen(true)} />
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
    </>
  );
}
