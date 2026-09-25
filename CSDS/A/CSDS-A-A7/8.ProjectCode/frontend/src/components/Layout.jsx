import { Link, useLocation, useNavigate } from "react-router-dom";
import { Shield, Home, Route as RouteIcon, Users, MessageCircle, LogOut } from "lucide-react";
import { useAuth } from "../AuthContext";

const NAV_ITEMS = [
  { to: "/home", label: "Home", icon: Home },
  { to: "/route", label: "Route", icon: RouteIcon },
  { to: "/assistant", label: "Assistant", icon: MessageCircle },
  { to: "/guardians", label: "Guardians", icon: Users },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col bg-slate-950">
      <header className="border-b border-slate-800 px-4 py-3 flex items-center justify-between">
        <Link to="/home" className="flex items-center gap-2 font-bold text-lg text-brand-400">
          <Shield size={22} /> SHEGUARD
        </Link>
        {user && (
          <button
            onClick={() => {
              logout();
              navigate("/login");
            }}
            className="flex items-center gap-1 text-sm text-slate-400 hover:text-brand-400"
          >
            <LogOut size={16} /> Log out
          </button>
        )}
      </header>

      <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-4">{children}</main>

      {user && (
        <nav className="border-t border-slate-800 bg-slate-950 sticky bottom-0">
          <div className="max-w-3xl mx-auto grid grid-cols-4">
            {NAV_ITEMS.map(({ to, label, icon: Icon }) => {
              const active = location.pathname.startsWith(to);
              return (
                <Link
                  key={to}
                  to={to}
                  className={`flex flex-col items-center gap-1 py-2 text-xs ${
                    active ? "text-brand-400" : "text-slate-500"
                  }`}
                >
                  <Icon size={20} />
                  {label}
                </Link>
              );
            })}
          </div>
        </nav>
      )}
    </div>
  );
}
