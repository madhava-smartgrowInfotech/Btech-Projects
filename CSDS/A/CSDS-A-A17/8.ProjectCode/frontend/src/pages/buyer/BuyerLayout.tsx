import { Outlet } from "react-router-dom";
import { LayoutGrid, ShoppingBag } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";

const navItems = [
  { to: "/buyer", label: "Marketplace", icon: LayoutGrid, end: true },
  { to: "/buyer/orders", label: "My orders", icon: ShoppingBag },
];

export function BuyerLayout() {
  return (
    <DashboardShell navItems={navItems} roleLabel="Buyer">
      <Outlet />
    </DashboardShell>
  );
}
