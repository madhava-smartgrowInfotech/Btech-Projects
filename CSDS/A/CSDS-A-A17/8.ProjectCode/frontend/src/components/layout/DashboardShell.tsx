import type { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { Leaf, LogOut } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useAuthStore } from "@/lib/authStore";
import { Avatar } from "@/components/ui/Avatar";
import { cn } from "@/lib/format";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
}

export function DashboardShell({
  navItems,
  roleLabel,
  children,
}: {
  navItems: NavItem[];
  roleLabel: string;
  children: ReactNode;
}) {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-sand-50 flex">
      <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-ink-100 bg-white">
        <div className="h-16 flex items-center gap-2 px-5 border-b border-ink-100">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
            <Leaf size={17} />
          </span>
          <span className="font-display font-semibold text-ink-900">CropSight</span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-xl px-3 h-10 text-sm font-medium transition-colors",
                  isActive ? "bg-brand-50 text-brand-700" : "text-ink-600 hover:bg-ink-50 hover:text-ink-900"
                )
              }
            >
              <item.icon size={17} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-ink-100">
          <div className="flex items-center gap-2.5 px-2 py-2 rounded-xl">
            <Avatar name={user?.name ?? "?"} />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-ink-900 truncate">{user?.name}</p>
              <p className="text-xs text-ink-500">{roleLabel}</p>
            </div>
            <button
              onClick={() => {
                logout();
                navigate("/");
              }}
              className="text-ink-400 hover:text-rose-600"
              title="Sign out"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      <div className="flex-1 min-w-0">
        <div className="md:hidden h-14 flex items-center justify-between px-4 border-b border-ink-100 bg-white">
          <span className="font-display font-semibold text-ink-900">CropSight</span>
          <Avatar name={user?.name ?? "?"} className="h-8 w-8 text-xs" />
        </div>
        <main className="p-5 sm:p-8 max-w-6xl mx-auto">{children}</main>
      </div>
    </div>
  );
}
