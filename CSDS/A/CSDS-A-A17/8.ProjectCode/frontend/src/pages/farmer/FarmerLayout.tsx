import { Outlet } from "react-router-dom";
import { LayoutGrid, PackageSearch } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";

const navItems = [
  { to: "/farmer", label: "Dashboard", icon: LayoutGrid, end: true },
  { to: "/farmer/orders", label: "Orders", icon: PackageSearch },
];

export function FarmerLayout() {
  return (
    <DashboardShell navItems={navItems} roleLabel="Farmer">
      <Outlet />
    </DashboardShell>
  );
}
