import { Link, useRouteError } from "react-router-dom";
import { Compass, TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LogoMark } from "@/components/brand/Logo";
import { useI18n } from "@/lib/i18n";

export default function NotFound() {
  const { t } = useI18n();
  return (
    <div className="grid min-h-[60dvh] place-items-center px-4 text-center">
      <div>
        <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-muted">
          <Compass className="h-7 w-7 text-muted-foreground" />
        </div>
        <h1 className="font-display text-2xl font-semibold">404</h1>
        <p className="mt-1 text-muted-foreground">{t("error.not_found")}</p>
        <Button asChild className="mt-6">
          <Link to="/app">{t("error.go_home")}</Link>
        </Button>
      </div>
    </div>
  );
}

/** Shown when a route throws (for example a failed lazy import after an update). */
export function RouteError() {
  const error = useRouteError() as Error | undefined;
  return (
    <div className="grid min-h-dvh place-items-center bg-background px-4 text-center">
      <div className="max-w-md">
        <LogoMark className="mx-auto mb-4 h-12 w-12" />
        <TriangleAlert className="mx-auto mb-2 h-6 w-6 text-caution" />
        <h1 className="font-display text-xl font-semibold">Something went wrong</h1>
        <p className="mt-2 text-sm text-muted-foreground">{error?.message ?? "Please reload the page."}</p>
        <div className="mt-6 flex justify-center gap-2">
          <Button onClick={() => window.location.reload()}>Reload</Button>
          <Button variant="outline" asChild>
            <a href="/app">Home</a>
          </Button>
        </div>
      </div>
    </div>
  );
}
