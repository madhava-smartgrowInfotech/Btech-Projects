import { motion, useReducedMotion, type HTMLMotionProps } from "framer-motion";

/** Plain opacity fade - also what every other entrance collapses to under reduced motion. */
export function FadeIn({
  delay = 0,
  duration = 0.5,
  ...props
}: HTMLMotionProps<"div"> & { delay?: number; duration?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration, delay, ease: "easeOut" }}
      {...props}
    />
  );
}

/** Fade + small lift that plays once the element scrolls into view. */
export function FadeInView({ delay = 0, ...props }: HTMLMotionProps<"div"> & { delay?: number }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      initial={{ opacity: 0, y: reduce ? 0 : 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
      {...props}
    />
  );
}
