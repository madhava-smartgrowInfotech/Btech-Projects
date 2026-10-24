import { Compass } from "lucide-react";
import { Link } from "react-router";

import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/Feedback";

export default function NotFound({ standalone = false }: { standalone?: boolean }) {
  const body = (
    <EmptyState
      icon={<Compass />}
      title="Page not found"
      description="That address doesn't exist in AgriVision. Head back to the dashboard or the home page."
      action={
        <>
          <Button asChild>
            <Link to="/dashboard">Open the dashboard</Link>
          </Button>
          <Button asChild variant="secondary">
            <Link to="/">Home</Link>
          </Button>
        </>
      }
    />
  );
  if (!standalone) return body;
  return (
    <>
      <AuroraBackground />
      <main className="grid min-h-dvh place-items-center px-4">
        <div className="w-full max-w-lg">{body}</div>
      </main>
    </>
  );
}
