import { Outlet } from "react-router-dom";
import { Gauge, BrainCircuit } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";

const navItems = [
  { to: "/admin", label: "Overview", icon: Gauge, end: true },
  { to: "/admin/models", label: "Model insights", icon: BrainCircuit },
];

export function AdminLayout() {
  return (
    <DashboardShell navItems={navItems} roleLabel="Admin">
      <Outlet />
    </DashboardShell>
  );
}
