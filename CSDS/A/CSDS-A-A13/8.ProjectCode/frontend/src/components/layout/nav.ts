import { Database, LayoutDashboard, Settings, Upload, Users } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { Role } from "@/lib/types";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  roles: Role[];
  end?: boolean;
}

export interface NavSection {
  title?: string;
  items: NavItem[];
}

const ALL: Role[] = ["admin", "invigilator"];
const ADMIN: Role[] = ["admin"];

export const NAV: NavSection[] = [
  { items: [{ to: "/app", label: "Dashboard", icon: LayoutDashboard, roles: ALL, end: true }] },
  {
    title: "Prepare",
    items: [
      { to: "/app/import", label: "Import data", icon: Upload, roles: ADMIN },
      { to: "/app/data", label: "Data", icon: Database, roles: ADMIN },
    ],
  },
  {
    title: "Workspace",
    items: [
      { to: "/app/team", label: "Team", icon: Users, roles: ADMIN },
      { to: "/app/settings", label: "Settings", icon: Settings, roles: ADMIN },
    ],
  },
];
