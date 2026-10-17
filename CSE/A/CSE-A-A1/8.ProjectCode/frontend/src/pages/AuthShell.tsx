import type { ReactNode } from "react";
import { Link } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { FadeIn } from "@/components/motion/FadeIn";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { ThemeToggle } from "@/components/ui/AppShell";
import { Card } from "@/components/ui/Card";

/** Centered glass card over the aurora, shared by sign in and register. */
export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <div className="relative grid min-h-dvh place-items-center px-4 py-10">
      <AuroraBackground />
      <div className="absolute right-3 top-3">
        <ThemeToggle />
      </div>
      <FadeIn className="w-full max-w-md space-y-6">
        <Link to="/" className="flex justify-center" aria-label="Adaptive Learning home">
          <Logo />
        </Link>
        <Card strong sweep={false} className="space-y-6 p-6 sm:p-8">
          <div className="space-y-1.5 text-center">
            <h1 className="font-display text-2xl font-semibold">{title}</h1>
            <p className="text-sm text-muted-foreground">{subtitle}</p>
          </div>
          {children}
        </Card>
        <p className="text-center text-sm text-muted-foreground">{footer}</p>
      </FadeIn>
    </div>
  );
}
