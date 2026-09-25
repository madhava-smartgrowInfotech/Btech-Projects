import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./AuthContext";
import Layout from "./components/Layout";
import { Loading } from "./components/StatusMessage";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Home from "./pages/Home";
import RoutePlanner from "./pages/RoutePlanner";
import EmergencySession from "./pages/EmergencySession";
import GuardianTrack from "./pages/GuardianTrack";
import Guardians from "./pages/Guardians";
import Assistant from "./pages/Assistant";

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <Loading label="Checking session..." />;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/track/:token" element={<GuardianTrack />} />

      <Route
        path="/home"
        element={
          <Protected>
            <Layout>
              <Home />
            </Layout>
          </Protected>
        }
      />
      <Route
        path="/route"
        element={
          <Protected>
            <Layout>
              <RoutePlanner />
            </Layout>
          </Protected>
        }
      />
      <Route
        path="/emergency/:sessionId"
        element={
          <Protected>
            <Layout>
              <EmergencySession />
            </Layout>
          </Protected>
        }
      />
      <Route
        path="/guardians"
        element={
          <Protected>
            <Layout>
              <Guardians />
            </Layout>
          </Protected>
        }
      />
      <Route
        path="/assistant"
        element={
          <Protected>
            <Layout>
              <Assistant />
            </Layout>
          </Protected>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
