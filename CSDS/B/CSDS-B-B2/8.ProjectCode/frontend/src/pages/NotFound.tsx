import { Link } from "react-router-dom";
import { MapPinOff } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-[60dvh] flex-col items-center justify-center px-4 text-center">
      <div className="mb-4 rounded-full bg-primary/10 p-4 text-primary">
        <MapPinOff className="h-8 w-8" aria-hidden />
      </div>
      <h1 className="text-2xl font-bold">No signal here</h1>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">This page doesn't exist or has moved.</p>
      <Button asChild className="mt-6">
        <Link to="/">Back to SignalScout</Link>
      </Button>
    </div>
  );
}
