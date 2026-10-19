import { Compass } from "lucide-react";
import { Link } from "react-router";

import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/Feedback";
import { HOME_BY_ROLE, useAuth } from "@/lib/auth";

export default function NotFound({ standalone = false }: { standalone?: boolean }) {
  const { user } = useAuth();
  const body = (
    <EmptyState
      icon={<Compass />}
      title="Page not found"
      description="This address does not exist in AegisBallot. Check the link or head back to a page that does."
      action={
        <Button asChild>
          <Link to={user ? HOME_BY_ROLE[user.role] : "/"}>{user ? "Back to my dashboard" : "Back to home"}</Link>
        </Button>
      }
    />
  );
  if (!standalone) return body;
  return (
    <>
      <AuroraBackground />
      <main className="mx-auto grid min-h-dvh max-w-xl place-items-center px-4">{body}</main>
    </>
  );
}
