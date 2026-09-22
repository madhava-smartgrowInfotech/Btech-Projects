import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Bell, Check, FlaskConical, Languages, LogOut, Menu, Monitor, Moon, Sun } from "lucide-react";
import { Logo } from "@/components/brand/Logo";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { MOBILE_TABS, NAV_SECTIONS, type NavItem } from "@/components/layout/nav";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDateTime, initials } from "@/lib/format";
import { LANGUAGES, useI18n, type Language } from "@/lib/i18n";
import { useLiveUpdates } from "@/lib/live";
import { notificationText } from "@/lib/notifications";
import { useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";

interface Badges {
  collect: number;
  approvals: number;
  unread: number;
}

function useBadges() {
  return useQuery({
    queryKey: ["badges"],
    queryFn: async () => (await api.get<Badges>("/notifications/summary")).data,
    refetchInterval: 20_000,
  });
}

function NavEntry({ item, badges, onNavigate }: { item: NavItem; badges?: Badges; onNavigate?: () => void }) {
  const { t } = useI18n();
  const count = item.badgeKey && badges ? badges[item.badgeKey] : 0;
  return (
    <NavLink
      to={item.to}
      end={item.end}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
          isActive ? "bg-sidebar-accent text-primary" : "text-sidebar-foreground/75 hover:bg-sidebar-accent/70 hover:text-sidebar-foreground",
        )
      }
    >
      {({ isActive }) => (
        <>
          {isActive && <motion.span layoutId="nav-pill" className="absolute inset-y-1.5 left-0 w-1 rounded-full bg-primary" />}
          <item.icon className="h-[18px] w-[18px] shrink-0" />
          <span className="truncate">{t(item.label)}</span>
          {count > 0 && (
            <span className="ml-auto grid h-5 min-w-5 place-items-center rounded-full bg-danger px-1.5 text-2xs font-semibold text-danger-foreground">
              {count}
            </span>
          )}
        </>
      )}
    </NavLink>
  );
}

function NavSections({ onNavigate, badges }: { onNavigate?: () => void; badges?: Badges }) {
  const { t } = useI18n();
  const { user } = useAuth();
  return (
    <nav className="space-y-6" aria-label="Main">
      {NAV_SECTIONS.map((section) => {
        const items = section.items.filter((i) => !i.adminOnly || user?.role === "admin");
        if (!items.length) return null;
        return (
          <div key={section.title}>
            <p className="mb-2 px-3 text-2xs font-semibold uppercase tracking-wider text-muted-foreground">{t(section.title)}</p>
            <div className="space-y-0.5">
              {items.map((item) => (
                <NavEntry key={item.to} item={item} badges={badges} onNavigate={onNavigate} />
              ))}
            </div>
          </div>
        );
      })}
    </nav>
  );
}

function SandboxPill({ className }: { className?: string }) {
  const { t } = useI18n();
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-caution/40 bg-caution-soft px-2.5 py-1 text-2xs font-semibold text-caution",
        className,
      )}
    >
      <FlaskConical className="h-3 w-3" />
      {t("common.sandbox")}
    </span>
  );
}

function LanguageMenu() {
  const { lang, setLang, t } = useI18n();
  const { user } = useAuth();
  const qc = useQueryClient();
  const save = useMutation({
    mutationFn: (language: Language) => api.put("/settings", { language }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["settings"] });
      qc.invalidateQueries({ queryKey: ["me"] });
    },
  });
  const choose = (code: Language) => {
    setLang(code);
    if (user) save.mutate(code);
  };
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label={t("nav.language")}>
          <Languages className="h-[18px] w-[18px]" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-44">
        <DropdownMenuLabel>{t("nav.language")}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {LANGUAGES.map((l) => (
          <DropdownMenuItem key={l.code} onClick={() => choose(l.code)} className="justify-between">
            <span>{l.native}</span>
            {lang === l.code && <Check className="h-4 w-4 text-primary" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function ThemeMenu() {
  const { theme, setTheme, resolved } = useTheme();
  const { t } = useI18n();
  const options = [
    { value: "light" as const, label: t("theme.light"), icon: Sun },
    { value: "dark" as const, label: t("theme.dark"), icon: Moon },
    { value: "system" as const, label: t("theme.system"), icon: Monitor },
  ];
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label={t("nav.theme")}>
          {resolved === "dark" ? <Moon className="h-[18px] w-[18px]" /> : <Sun className="h-[18px] w-[18px]" />}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        {options.map((o) => (
          <DropdownMenuItem key={o.value} onClick={() => setTheme(o.value)} className="justify-between">
            <span className="flex items-center gap-2">
              <o.icon className="h-4 w-4" />
              {o.label}
            </span>
            {theme === o.value && <Check className="h-4 w-4 text-primary" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

interface NotificationItem {
  id: number;
  kind: string;
  payload: Record<string, unknown>;
  read: boolean;
  created_at: string;
}

function NotificationsBell({ unread }: { unread: number }) {
  const { t, tx, lang } = useI18n();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const list = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => (await api.get<{ unread: number; items: NotificationItem[] }>("/notifications")).data,
    enabled: open,
  });
  const markAll = useMutation({
    mutationFn: () => api.post("/notifications/read", {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
      qc.invalidateQueries({ queryKey: ["badges"] });
    },
  });
  const target = (n: NotificationItem) => {
    if (n.kind === "approval_requested") return "/app/approvals";
    if (n.kind === "collect_received") return "/app/collect";
    if (n.payload.transaction_id) return `/app/history/${n.payload.transaction_id}`;
    return "/app";
  };
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative" aria-label={t("nav.notifications")}>
          <Bell className="h-[18px] w-[18px]" />
          {unread > 0 && (
            <span className="absolute right-1.5 top-1.5 grid h-4 min-w-4 place-items-center rounded-full bg-danger px-1 text-[10px] font-bold text-danger-foreground">
              {unread > 9 ? "9+" : unread}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-[min(92vw,360px)] p-0">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <p className="font-medium">{t("nav.notifications")}</p>
          {unread > 0 && (
            <Button variant="ghost" size="sm" onClick={() => markAll.mutate()}>
              <Check className="mr-1 h-4 w-4" />
              {t("notif.mark_read")}
            </Button>
          )}
        </div>
        <ScrollArea className="max-h-[60vh]">
          {list.isLoading && <p className="p-4 text-sm text-muted-foreground">{t("common.loading")}</p>}
          {list.data && list.data.items.length === 0 && <p className="p-6 text-center text-sm text-muted-foreground">{t("notif.empty")}</p>}
          <ul>
            {list.data?.items.map((n) => {
              const text = notificationText(n.kind, n.payload, tx);
              return (
                <li key={n.id}>
                  <button
                    className={cn("flex w-full gap-3 border-b px-4 py-3 text-left transition-colors hover:bg-muted/60", !n.read && "bg-primary/5")}
                    onClick={() => {
                      setOpen(false);
                      navigate(target(n));
                    }}
                  >
                    <span className={cn("mt-1.5 h-2 w-2 shrink-0 rounded-full", n.read ? "bg-transparent" : "bg-primary")} />
                    <span className="min-w-0">
                      <span className="block text-sm font-medium">{text.title}</span>
                      {text.body && <span className="block text-xs text-muted-foreground">{text.body}</span>}
                      <span className="mt-0.5 block text-2xs text-muted-foreground">{formatDateTime(n.created_at, lang)}</span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}

function UserMenu() {
  const { user, logout } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  if (!user) return null;
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="grid h-9 w-9 place-items-center rounded-full bg-primary text-sm font-semibold text-primary-foreground" aria-label={user.full_name}>
          {initials(user.full_name)}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-60">
        <DropdownMenuLabel className="font-normal">
          <p className="font-medium">{user.full_name}</p>
          <p className="text-xs text-muted-foreground">{user.upi_id}</p>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => navigate("/app/settings")}>{t("nav.settings")}</DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => {
            logout();
            navigate("/login");
          }}
          className="text-danger focus:text-danger"
        >
          <LogOut className="mr-2 h-4 w-4" />
          {t("nav.logout")}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export default function AppLayout() {
  const { user } = useAuth();
  const { t } = useI18n();
  const location = useLocation();
  const reduce = useReducedMotion();
  const [moreOpen, setMoreOpen] = useState(false);
  const badges = useBadges();
  useLiveUpdates(!!user);

  return (
    <div className="min-h-dvh bg-background">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-sidebar-border bg-sidebar lg:flex">
        <div className="flex h-16 items-center px-5">
          <NavLink to="/app" aria-label="UPI Guardian home">
            <Logo />
          </NavLink>
        </div>
        <ScrollArea className="flex-1 px-3 py-2">
          <NavSections badges={badges.data} />
        </ScrollArea>
        <div className="border-t border-sidebar-border p-4">
          <SandboxPill />
          {user && (
            <div className="mt-3 flex items-center gap-3">
              <div className="grid h-9 w-9 place-items-center rounded-full bg-primary/15 text-sm font-semibold text-primary">{initials(user.full_name)}</div>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{user.full_name}</p>
                <p className="truncate text-xs text-muted-foreground">{user.upi_id}</p>
              </div>
              {user.is_sample && (
                <Badge variant="secondary" className="ml-auto shrink-0">
                  {t("common.sample")}
                </Badge>
              )}
            </div>
          )}
        </div>
      </aside>

      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-20 border-b bg-background/80 backdrop-blur-xl">
          <div className="flex h-14 items-center gap-2 px-4 sm:h-16 sm:px-6">
            <NavLink to="/app" className="lg:hidden" aria-label="UPI Guardian home">
              <Logo />
            </NavLink>
            <SandboxPill className="ml-2 hidden sm:inline-flex lg:ml-0" />
            <div className="ml-auto flex items-center gap-1">
              <LanguageMenu />
              <ThemeMenu />
              <NotificationsBell unread={badges.data?.unread ?? 0} />
              <div className="ml-1">
                <UserMenu />
              </div>
            </div>
          </div>
        </header>

        <main id="main" className="mx-auto w-full max-w-6xl px-4 pb-28 pt-5 sm:px-6 sm:pt-8 lg:pb-12">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={location.pathname}
              initial={reduce ? false : { opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={reduce ? undefined : { opacity: 0, y: -6 }}
              transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Mobile bottom tabs */}
      <nav
        className="fixed inset-x-0 bottom-0 z-30 border-t bg-background/90 pb-[env(safe-area-inset-bottom)] backdrop-blur-xl lg:hidden"
        aria-label="Quick"
      >
        <div className="mx-auto grid max-w-lg grid-cols-5">
          {MOBILE_TABS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn("flex flex-col items-center gap-1 py-2.5 text-[11px] font-medium", isActive ? "text-primary" : "text-muted-foreground")
              }
            >
              <item.icon className="h-5 w-5" />
              <span className="max-w-full truncate px-1">{t(item.label)}</span>
            </NavLink>
          ))}
          <Sheet open={moreOpen} onOpenChange={setMoreOpen}>
            <SheetTrigger asChild>
              <button className="relative flex flex-col items-center gap-1 py-2.5 text-[11px] font-medium text-muted-foreground">
                <Menu className="h-5 w-5" />
                <span>{t("nav.more")}</span>
                {(badges.data?.collect ?? 0) + (badges.data?.approvals ?? 0) > 0 && (
                  <span className="absolute right-[30%] top-2 h-2 w-2 rounded-full bg-danger" />
                )}
              </button>
            </SheetTrigger>
            <SheetContent side="bottom" className="max-h-[85dvh] overflow-y-auto rounded-t-2xl">
              <SheetHeader className="mb-4 text-left">
                <SheetTitle>
                  <Logo />
                </SheetTitle>
              </SheetHeader>
              <NavSections badges={badges.data} onNavigate={() => setMoreOpen(false)} />
              <SandboxPill className="mt-6" />
            </SheetContent>
          </Sheet>
        </div>
      </nav>
    </div>
  );
}
