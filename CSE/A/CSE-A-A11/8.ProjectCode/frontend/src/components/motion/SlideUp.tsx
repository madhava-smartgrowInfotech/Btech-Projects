import { motion, useReducedMotion, type HTMLMotionProps } from "framer-motion";

/** Lifts content into place; collapses to a fade when the user prefers reduced motion. */
export function SlideUp({
  delay = 0,
  distance = 16,
  ...props
}: HTMLMotionProps<"div"> & { delay?: number; distance?: number }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      initial={{ opacity: 0, y: reduce ? 0 : distance }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
      {...props}
    />
  );
}
