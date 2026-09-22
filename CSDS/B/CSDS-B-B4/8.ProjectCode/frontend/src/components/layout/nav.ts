import {
  BarChart3,
  Bell,
  BrainCircuit,
  FlaskConical,
  History,
  Home,
  MessageSquareWarning,
  QrCode,
  Send,
  Settings,
  ShieldCheck,
  Users,
  type LucideIcon,
} from "lucide-react";
import type { MessageKey } from "@/locales/en";

export interface NavItem {
  to: string;
  label: MessageKey;
  icon: LucideIcon;
  end?: boolean;
  badgeKey?: "collect" | "approvals";
  adminOnly?: boolean;
}

export interface NavSection {
  title: MessageKey;
  items: NavItem[];
}

export const NAV_SECTIONS: NavSection[] = [
  {
    title: "nav.section.pay",
    items: [
      { to: "/app", label: "nav.home", icon: Home, end: true },
      { to: "/app/send", label: "nav.send", icon: Send },
      { to: "/app/scan", label: "nav.scan", icon: QrCode },
      { to: "/app/collect", label: "nav.collect", icon: Bell, badgeKey: "collect" },
      { to: "/app/history", label: "nav.history", icon: History },
    ],
  },
  {
    title: "nav.section.protect",
    items: [
      { to: "/app/sms", label: "nav.sms", icon: MessageSquareWarning },
      { to: "/app/trusted", label: "nav.trusted", icon: Users },
      { to: "/app/approvals", label: "nav.approvals", icon: ShieldCheck, badgeKey: "approvals" },
      { to: "/app/settings", label: "nav.settings", icon: Settings },
    ],
  },
  {
    title: "nav.section.insights",
    items: [
      { to: "/admin", label: "nav.admin", icon: BarChart3, adminOnly: true },
      { to: "/app/models", label: "nav.models", icon: BrainCircuit },
      { to: "/app/sandbox", label: "nav.sandbox", icon: FlaskConical },
    ],
  },
];

export const MOBILE_TABS: NavItem[] = [
  { to: "/app", label: "nav.home", icon: Home, end: true },
  { to: "/app/send", label: "nav.send", icon: Send },
  { to: "/app/scan", label: "nav.scan", icon: QrCode },
  { to: "/app/sms", label: "nav.sms", icon: MessageSquareWarning },
];
