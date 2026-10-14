import { useLayoutEffect, useRef, type ReactNode } from "react";

import { gsap, ScrollTrigger } from "@/lib/gsap";
import { cn, prefersReducedMotion } from "@/lib/utils";

/**
 * Scroll reveal driven by GSAP ScrollTrigger. Children marked [data-reveal] animate in sequence
 * (or the wrapper itself when there are none). Reduced motion -> plain fade.
 */
export function Reveal({
  children,
  className,
  y = 32,
  stagger = 0.08,
}: {
  children: ReactNode;
  className?: string;
  y?: number;
  stagger?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const reduce = prefersReducedMotion();
    const marked = Array.from(el.querySelectorAll<HTMLElement>("[data-reveal]"));
    const targets: HTMLElement[] = marked.length ? marked : [el];
    const ctx = gsap.context(() => {
      gsap.fromTo(
        targets,
        { autoAlpha: 0, y: reduce ? 0 : y },
        {
          autoAlpha: 1,
          y: 0,
          duration: reduce ? 0.4 : 0.9,
          ease: "power3.out",
          stagger: reduce ? 0 : stagger,
          scrollTrigger: { trigger: el, start: "top 88%", once: true },
        },
      );
    }, el);
    ScrollTrigger.refresh();
    return () => ctx.revert();
  }, [y, stagger]);

  return (
    <div ref={ref} className={cn(className)}>
      {children}
    </div>
  );
}
