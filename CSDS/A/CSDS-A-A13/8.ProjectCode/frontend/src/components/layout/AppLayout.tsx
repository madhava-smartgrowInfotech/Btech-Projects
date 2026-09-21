import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { motion } from "motion/react";
import { LogOut, Menu } from "lucide-react";
import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { NAV } from "@/components/layout/nav";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet";
import { useAuth } from "@/lib/auth";
import { initials } from "@/lib/format";
import type { User } from "@/lib/types";
import { cn } from "@/lib/utils";

function SidebarNav({ user, onNavigate }: { user: User; onNavigate?: () => void }) {
  return (
    <nav className="flex flex-1 flex-col gap-5 overflow-y-auto px-3 py-4 scrollbar-thin" aria-label="Main">
      {NAV.map((section, i) => {
        const items = section.items.filter((item) => item.roles.includes(user.role));
        if (!items.length) return null;
        return (
          <div key={section.title ?? i}>
            {section.title && (
              <div className="mb-1.5 px-3 text-2xs font-semibold uppercase tracking-wider text-muted-foreground">{section.title}</div>
            )}
            <ul className="space-y-0.5">
              {items.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.end}
                    onClick={onNavigate}
                    className={({ isActive }) =>
                      cn(
                        "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-sidebar-foreground/80 transition-colors hover:bg-accent hover:text-foreground",
                        isActive && "bg-primary/10 text-primary hover:bg-primary/10 hover:text-primary",
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <motion.span
                            layoutId="nav-active"
                            className="absolute inset-y-1.5 left-0 w-[3px] rounded-full bg-primary"
                            transition={{ type: "spring", stiffness: 500, damping: 40 }}
                          />
                        )}
                        <item.icon className="size-[18px] shrink-0" aria-hidden />
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

function UserMenu({ user }: { user: User }) {
  const { logout } = useAuth();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className="flex w-full items-center gap-3 rounded-lg p-2 text-left transition-colors hover:bg-accent"
          aria-label="Account menu"
        >
          <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary/15 text-sm font-semibold text-primary">
            {initials(user.full_name)}
          </span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-medium">{user.full_name}</span>
            <span className="block truncate text-xs capitalize text-muted-foreground">{user.role}</span>
          </span>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-60">
        <DropdownMenuLabel className="font-normal">
          <div className="text-sm font-medium text-foreground">{user.full_name}</div>
          <div className="truncate text-xs">{user.email}</div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => logout("You have signed out.")}>
          <LogOut /> Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function AppLayout() {
  const { user } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [location.pathname]);

  if (!user) return null;

  return (
    <div className="min-h-dvh lg:pl-64">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-sidebar-border bg-sidebar lg:flex">
        <div className="flex h-16 items-center justify-between px-5">
          <Link to="/app" aria-label="SeatWise dashboard">
            <Logo />
          </Link>
          <ThemeToggle />
        </div>
        <SidebarNav user={user} />
        <div className="border-t border-sidebar-border p-3">
          <UserMenu user={user} />
        </div>
      </aside>

      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b bg-background/85 px-3 backdrop-blur lg:hidden">
        <Button variant="ghost" size="icon" aria-label="Open menu" onClick={() => setMenuOpen(true)}>
          <Menu />
        </Button>
        <Link to="/app" aria-label="SeatWise dashboard">
          <Logo markClassName="size-7" />
        </Link>
        <ThemeToggle />
      </header>

      <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
        <SheetContent side="left" className="p-0">
          <SheetTitle className="sr-only">Menu</SheetTitle>
          <SheetDescription className="sr-only">Main navigation</SheetDescription>
          <div className="flex h-14 items-center px-5">
            <Logo />
          </div>
          <SidebarNav user={user} onNavigate={() => setMenuOpen(false)} />
          <div className="border-t border-sidebar-border p-3">
            <UserMenu user={user} />
          </div>
        </SheetContent>
      </Sheet>

      <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        {user.role === "invigilator" && (
          <Badge variant="secondary" className="mb-4 lg:hidden">
            Invigilator view
          </Badge>
        )}
        {/* Enter-only transition: the new page fades in without waiting for the old one to leave. */}
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
        >
          <Outlet />
        </motion.div>
      </main>
    </div>
  );
}
