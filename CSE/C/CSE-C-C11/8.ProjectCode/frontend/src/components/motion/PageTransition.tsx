import { motion, useReducedMotion, type HTMLMotionProps } from "framer-motion";

/**
 * Route transition: incoming content lifts 12px and fades in, the outgoing view scales down
 * slightly and fades. Use inside <AnimatePresence mode="wait">. Reduced motion -> plain fade.
 */
export function PageTransition(props: HTMLMotionProps<"div">) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      initial={{ opacity: 0, y: reduce ? 0 : 12, scale: 1 }}
      animate={{ opacity: 1, y: 0, scale: 1, transition: { duration: 0.42, ease: [0.22, 1, 0.36, 1] } }}
      exit={{ opacity: 0, y: 0, scale: reduce ? 1 : 0.98, transition: { duration: 0.18, ease: "easeIn" } }}
      style={{ transformOrigin: "50% 0%" }}
      {...props}
    />
  );
}
