import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/brand/Logo";
import { useI18n } from "@/lib/i18n";

export default function Landing() {
  const { t } = useI18n();
  return (
    <div className="min-h-dvh bg-background">
      <header className="container flex h-16 items-center justify-between">
        <Logo />
        <Button asChild variant="ghost">
          <Link to="/login">{t("auth.login.link")}</Link>
        </Button>
      </header>
      <main id="main" className="container grid min-h-[70dvh] place-items-center text-center">
        <div className="max-w-2xl">
          <h1 className="font-display text-4xl font-semibold tracking-tight sm:text-6xl">{t("app.tagline")}</h1>
          <Button asChild size="lg" className="mt-8">
            <Link to="/register">
              {t("auth.register.link")}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </main>
    </div>
  );
}
