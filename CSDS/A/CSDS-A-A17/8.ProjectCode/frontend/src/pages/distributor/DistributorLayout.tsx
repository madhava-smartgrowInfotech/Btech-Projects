import { Outlet } from "react-router-dom";
import { Truck } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";

const navItems = [{ to: "/distributor", label: "Active deliveries", icon: Truck, end: true }];

export function DistributorLayout() {
  return (
    <DashboardShell navItems={navItems} roleLabel="Distributor">
      <Outlet />
    </DashboardShell>
  );
}
