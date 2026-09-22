import type { LucideIcon } from "lucide-react";
import { Cpu, LayoutDashboard, Map, QrCode, Users } from "lucide-react";
import type { Role } from "@/lib/api";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  minRole: Role;
  end?: boolean;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

export const NAV: NavSection[] = [
  {
    title: "Overview",
    items: [
      { to: "/app", label: "Dashboard", icon: LayoutDashboard, minRole: "user", end: true },
      { to: "/app/map", label: "Coverage map", icon: Map, minRole: "user" },
    ],
  },
  {
    title: "Field",
    items: [
      { to: "/app/connect", label: "Connect a phone", icon: QrCode, minRole: "user" },
      { to: "/app/devices", label: "Devices", icon: Cpu, minRole: "user" },
    ],
  },
  {
    title: "Administration",
    items: [{ to: "/app/admin/users", label: "Users", icon: Users, minRole: "admin" }],
  },
];
