import type { LucideIcon } from "lucide-react";
import { Cpu, FileWarning, Headset, LayoutDashboard, Map, QrCode, Settings, Smartphone, Users } from "lucide-react";
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
      { to: "/app/complaints", label: "My complaints", icon: FileWarning, minRole: "user" },
    ],
  },
  {
    title: "Field",
    items: [
      { to: "/probe", label: "Field probe", icon: Smartphone, minRole: "user" },
      { to: "/app/connect", label: "Connect a phone", icon: QrCode, minRole: "user" },
      { to: "/app/devices", label: "Devices", icon: Cpu, minRole: "user" },
    ],
  },
  {
    title: "Operations",
    items: [{ to: "/app/desk", label: "Operator desk", icon: Headset, minRole: "engineer" }],
  },
  {
    title: "Administration",
    items: [
      { to: "/app/settings", label: "Settings", icon: Settings, minRole: "admin" },
      { to: "/app/admin/users", label: "Users", icon: Users, minRole: "admin" },
    ],
  },
];
