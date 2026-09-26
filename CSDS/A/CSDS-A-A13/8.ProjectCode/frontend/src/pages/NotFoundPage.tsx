import { Link } from "react-router-dom";
import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-6 px-4 text-center">
      <Logo />
      <div>
        <div className="font-display text-6xl font-semibold text-primary">404</div>
        <h1 className="mt-2 text-xl font-semibold">This page is not on the seating plan</h1>
        <p className="mt-2 text-sm text-muted-foreground">The address may be mistyped, or the page has moved.</p>
      </div>
      <div className="flex gap-2">
        <Button asChild>
          <Link to="/">Go to the home page</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/app">Open the dashboard</Link>
        </Button>
      </div>
    </div>
  );
}
