import Lenis from "lenis";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

let lenis: Lenis | null = null;

export function startSmoothScroll(): () => void {
  lenis = new Lenis({ duration: 1.05, smoothWheel: true });

  lenis.on("scroll", ScrollTrigger.update);

  gsap.ticker.add((time) => {
    lenis?.raf(time * 1000);
  });
  gsap.ticker.lagSmoothing(0);

  return () => {
    lenis?.destroy();
    lenis = null;
  };
}

export function getLenis() {
  return lenis;
}

export { gsap, ScrollTrigger };
