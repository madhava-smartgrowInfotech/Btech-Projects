import { Compass } from "lucide-react";
import { Link } from "react-router";

import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/Feedback";

export default function NotFound() {
  return (
    <div className="mx-auto grid min-h-[60dvh] max-w-lg place-items-center px-4">
      <EmptyState
        icon={<Compass />}
        title="That page doesn't exist"
        description="The link may be old, or the review it pointed to was deleted."
        action={
          <>
            <Button asChild>
              <Link to="/app">Go to overview</Link>
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
