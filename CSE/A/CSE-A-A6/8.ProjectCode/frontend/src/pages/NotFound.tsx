import { Compass } from "lucide-react";
import { Link } from "react-router";

import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/Feedback";

export default function NotFound() {
  return (
    <div className="grid min-h-[60dvh] place-items-center px-4">
      <EmptyState
        icon={<Compass />}
        title="This page doesn't exist"
        description="The address may be mistyped or the page has moved. Head back to the monitor."
        action={
          <>
            <Button asChild>
              <Link to="/app">Open the monitor</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link to="/">Home</Link>
            </Button>
          </>
        }
      />
    </div>
  );
}
