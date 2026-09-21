import { ArrowLeft, SearchX } from "lucide-react";
import { Link } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="grid min-h-dvh place-items-center px-4">
      <div className="max-w-md space-y-5 text-center">
        <Logo className="justify-center" />
        <SearchX className="mx-auto size-12 text-muted-foreground" />
        <h1 className="text-2xl font-bold">This page isn't in the policy</h1>
        <p className="text-muted-foreground">The page you're looking for doesn't exist or has moved.</p>
        <Button asChild>
          <Link to="/">
            <ArrowLeft /> Back to PolicyLens
          </Link>
        </Button>
      </div>
    </div>
  );
}
