import { Route, Routes } from "react-router-dom";
import { RequireRole } from "@/components/RequireRole";
import { Toaster } from "@/components/ui/Toast";

import { Landing } from "@/pages/marketing/Landing";
import { Login } from "@/pages/auth/Login";
import { Signup } from "@/pages/auth/Signup";

import { FarmerLayout } from "@/pages/farmer/FarmerLayout";
import { FarmerDashboard } from "@/pages/farmer/FarmerDashboard";
import { ListingWorkspace } from "@/pages/farmer/ListingWorkspace";
import { FarmerOrders } from "@/pages/farmer/FarmerOrders";

import { BuyerLayout } from "@/pages/buyer/BuyerLayout";
import { Marketplace } from "@/pages/buyer/Marketplace";
import { ListingDetail } from "@/pages/buyer/ListingDetail";
import { BuyerOrders } from "@/pages/buyer/BuyerOrders";

import { DistributorLayout } from "@/pages/distributor/DistributorLayout";
import { ActiveDeliveries } from "@/pages/distributor/ActiveDeliveries";
import { LiveMonitoring } from "@/pages/distributor/LiveMonitoring";

import { AdminLayout } from "@/pages/admin/AdminLayout";
import { Overview } from "@/pages/admin/Overview";
import { ModelInsights } from "@/pages/admin/ModelInsights";

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        <Route
          path="/farmer"
          element={
            <RequireRole role="farmer">
              <FarmerLayout />
            </RequireRole>
          }
        >
          <Route index element={<FarmerDashboard />} />
          <Route path="listings/:id" element={<ListingWorkspace />} />
          <Route path="orders" element={<FarmerOrders />} />
        </Route>

        <Route
          path="/buyer"
          element={
            <RequireRole role="buyer">
              <BuyerLayout />
            </RequireRole>
          }
        >
          <Route index element={<Marketplace />} />
          <Route path="listings/:id" element={<ListingDetail />} />
          <Route path="orders" element={<BuyerOrders />} />
        </Route>

        <Route
          path="/distributor"
          element={
            <RequireRole role="distributor">
              <DistributorLayout />
            </RequireRole>
          }
        >
          <Route index element={<ActiveDeliveries />} />
          <Route path="shipments/:id" element={<LiveMonitoring />} />
        </Route>

        <Route
          path="/admin"
          element={
            <RequireRole role="admin">
              <AdminLayout />
            </RequireRole>
          }
        >
          <Route index element={<Overview />} />
          <Route path="models" element={<ModelInsights />} />
        </Route>
      </Routes>
      <Toaster />
    </>
  );
}
