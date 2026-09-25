import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext.jsx";
import Navbar from "./components/Navbar.jsx";
import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Upload from "./pages/Upload.jsx";
import ContractList from "./pages/ContractList.jsx";
import ContractReport from "./pages/ContractReport.jsx";
import ClauseDetail from "./pages/ClauseDetail.jsx";
import ClauseGraph from "./pages/ClauseGraph.jsx";
import Evaluation from "./pages/Evaluation.jsx";

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <main className="mx-auto max-w-6xl px-4 py-6">
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/evaluation" element={<Evaluation />} />
            <Route
              path="/upload"
              element={
                <ProtectedRoute>
                  <Upload />
                </ProtectedRoute>
              }
            />
            <Route
              path="/contracts"
              element={
                <ProtectedRoute>
                  <ContractList />
                </ProtectedRoute>
              }
            />
            <Route
              path="/contracts/:id"
              element={
                <ProtectedRoute>
                  <ContractReport />
                </ProtectedRoute>
              }
            />
            <Route
              path="/contracts/:id/clauses/:clauseId"
              element={
                <ProtectedRoute>
                  <ClauseDetail />
                </ProtectedRoute>
              }
            />
            <Route
              path="/contracts/:id/graph"
              element={
                <ProtectedRoute>
                  <ClauseGraph />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </AuthProvider>
  );
}
