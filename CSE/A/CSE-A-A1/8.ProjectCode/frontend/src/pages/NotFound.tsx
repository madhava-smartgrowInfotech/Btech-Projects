import { Compass } from "lucide-react";
import { Link } from "react-router";

import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/Feedback";

export default function NotFound() {
  return (
    <div className="grid min-h-dvh place-items-center px-4">
      <AuroraBackground />
      <EmptyState
        className="w-full max-w-md"
        icon={<Compass />}
        title="That page doesn't exist"
        description="The link may be old or mistyped. Head back to the start and pick up where you left off."
        action={
          <Button asChild>
            <Link to="/">Back to home</Link>
          </Button>
        }
      />
    </div>
  );
}
