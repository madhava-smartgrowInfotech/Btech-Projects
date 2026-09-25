import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Leaf, Menu, X } from "lucide-react";
import { useAuthStore } from "@/lib/authStore";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/format";

const ROLE_HOME: Record<string, string> = {
  farmer: "/farmer",
  buyer: "/buyer",
  distributor: "/distributor",
  admin: "/admin",
};

const LINKS = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#features", label: "Platform" },
  { href: "#intelligence", label: "Intelligence" },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "fixed top-0 inset-x-0 z-50 transition-all duration-300",
        scrolled ? "bg-white/80 backdrop-blur-lg border-b border-ink-100 shadow-sm" : "bg-transparent"
      )}
    >
      <div className="mx-auto max-w-7xl px-5 sm:px-8 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-display font-semibold text-lg text-ink-900">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
            <Leaf size={17} />
          </span>
          CropSight
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          {LINKS.map((l) => (
            <a key={l.href} href={l.href} className="text-sm font-medium text-ink-600 hover:text-ink-900 transition-colors">
              {l.label}
            </a>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-3">
          {user ? (
            <>
              <Button variant="ghost" size="sm" onClick={() => navigate(ROLE_HOME[user.role] ?? "/")}>
                Dashboard
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  logout();
                  navigate("/");
                }}
              >
                Sign out
              </Button>
            </>
          ) : (
            <>
              <Button variant="ghost" size="sm" onClick={() => navigate("/login")}>
                Log in
              </Button>
              <Button size="sm" onClick={() => navigate("/signup")}>
                Get started
              </Button>
            </>
          )}
        </div>

        <button className="md:hidden text-ink-700" onClick={() => setOpen((o) => !o)}>
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {open && (
        <div className="md:hidden bg-white border-t border-ink-100 px-5 py-4 flex flex-col gap-3">
          {LINKS.map((l) => (
            <a key={l.href} href={l.href} className="text-sm font-medium text-ink-700" onClick={() => setOpen(false)}>
              {l.label}
            </a>
          ))}
          <div className="flex gap-2 pt-2">
            {user ? (
              <Button className="flex-1" size="sm" onClick={() => navigate(ROLE_HOME[user.role] ?? "/")}>
                Dashboard
              </Button>
            ) : (
              <>
                <Button variant="outline" className="flex-1" size="sm" onClick={() => navigate("/login")}>
                  Log in
                </Button>
                <Button className="flex-1" size="sm" onClick={() => navigate("/signup")}>
                  Get started
                </Button>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
