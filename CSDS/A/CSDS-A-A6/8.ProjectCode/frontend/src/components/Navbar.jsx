import { Link, useNavigate } from "react-router-dom";
import { ShieldCheck, LogOut } from "lucide-react";
import { useAuth } from "../AuthContext.jsx";

export default function Navbar() {
  const { isAuthenticated, email, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <nav className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link to="/" className="flex items-center gap-2 font-semibold text-slate-900">
          <ShieldCheck className="h-6 w-6 text-brand-600" />
          ClauseGuard
        </Link>
        <div className="flex items-center gap-4 text-sm">
          {isAuthenticated ? (
            <>
              <Link to="/upload" className="text-slate-600 hover:text-brand-600">Upload</Link>
              <Link to="/contracts" className="text-slate-600 hover:text-brand-600">My Contracts</Link>
              <Link to="/evaluation" className="text-slate-600 hover:text-brand-600">Evaluation</Link>
              <span className="text-slate-400">{email}</span>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1 rounded-md border border-slate-300 px-3 py-1.5 text-slate-700 hover:bg-slate-100"
              >
                <LogOut className="h-4 w-4" /> Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/evaluation" className="text-slate-600 hover:text-brand-600">Evaluation</Link>
              <Link to="/login" className="text-slate-600 hover:text-brand-600">Log in</Link>
              <Link
                to="/register"
                className="rounded-md bg-brand-600 px-3 py-1.5 text-white hover:bg-brand-700"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
