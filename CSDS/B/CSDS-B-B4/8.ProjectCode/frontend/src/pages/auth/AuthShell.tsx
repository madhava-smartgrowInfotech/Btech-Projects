import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { BellRing, MessageSquareWarning, ShieldCheck } from "lucide-react";
import { Logo } from "@/components/brand/Logo";
import { ThemeMenu } from "@/components/layout/AppLayout";
import { LANGUAGES, useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export function AuthShell({ children }: { children: ReactNode }) {
  const { t, lang, setLang } = useI18n();
  const points = [
    { icon: ShieldCheck, text: t("auth.side.point1") },
    { icon: MessageSquareWarning, text: t("auth.side.point2") },
    { icon: BellRing, text: t("auth.side.point3") },
  ];
  return (
    <div className="grid min-h-dvh lg:grid-cols-[1.05fr_1fr]">
      <aside className="relative hidden overflow-hidden bg-[#071a1a] text-white lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div className="pointer-events-none absolute inset-0 opacity-70 [background:radial-gradient(60%_50%_at_20%_10%,rgba(45,212,191,0.35),transparent_60%),radial-gradient(40%_40%_at_90%_80%,rgba(245,158,11,0.22),transparent_60%)]" />
        <div className="pointer-events-none absolute inset-0 opacity-[0.07] grid-bg" />
        <Link to="/" className="relative">
          <Logo className="[&_span]:text-white" />
        </Link>
        <div className="relative max-w-md">
          <h2 className="font-display text-4xl font-semibold leading-tight">{t("auth.side.title")}</h2>
          <ul className="mt-8 space-y-4">
            {points.map((p, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.15 + i * 0.1 }}
                className="flex items-start gap-3"
              >
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-white/10 text-teal-300">
                  <p.icon className="h-5 w-5" />
                </span>
                <span className="pt-1.5 text-white/85">{p.text}</span>
              </motion.li>
            ))}
          </ul>
        </div>
        <p className="relative text-xs text-white/50">{t("common.sandbox")}</p>
      </aside>

      <section className="flex flex-col">
        <div className="flex items-center justify-between p-4 sm:p-6">
          <Link to="/" className="lg:invisible">
            <Logo />
          </Link>
          <div className="flex items-center gap-1">
            <div className="flex rounded-full border p-0.5" role="group" aria-label={t("nav.language")}>
              {LANGUAGES.map((l) => (
                <button
                  key={l.code}
                  onClick={() => setLang(l.code)}
                  className={cn(
                    "rounded-full px-2.5 py-1 text-xs font-medium transition-colors",
                    lang === l.code ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground",
                  )}
                  aria-pressed={lang === l.code}
                >
                  {l.native}
                </button>
              ))}
            </div>
            <ThemeMenu />
          </div>
        </div>
        <div className="flex flex-1 items-start justify-center px-4 pb-12 pt-4 sm:items-center sm:px-6">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
            {children}
          </motion.div>
        </div>
      </section>
    </div>
  );
}
