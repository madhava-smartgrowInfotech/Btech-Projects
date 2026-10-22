import { useReducedMotion } from "framer-motion";

/** True when the user asked the OS for less motion: charts then skip their draw-in animation. */
export function useReducedMotionFlag(): boolean {
  return !!useReducedMotion();
}
