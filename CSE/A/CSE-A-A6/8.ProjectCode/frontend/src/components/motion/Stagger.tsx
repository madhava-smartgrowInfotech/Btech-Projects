import { motion, useReducedMotion, type HTMLMotionProps, type Variants } from "framer-motion";

/** Parent that reveals its <StaggerItem> children one after another. */
export function Stagger({
  gap = 0.06,
  delay = 0,
  inView = false,
  ...props
}: HTMLMotionProps<"div"> & { gap?: number; delay?: number; inView?: boolean }) {
  const variants: Variants = {
    hidden: {},
    show: { transition: { staggerChildren: gap, delayChildren: delay } },
  };
  return (
    <motion.div
      variants={variants}
      initial="hidden"
      {...(inView ? { whileInView: "show", viewport: { once: true, margin: "-40px" } } : { animate: "show" })}
      {...props}
    />
  );
}

export function StaggerItem(props: HTMLMotionProps<"div">) {
  const reduce = useReducedMotion();
  const variants: Variants = {
    hidden: { opacity: 0, y: reduce ? 0 : 14, scale: reduce ? 1 : 0.985 },
    show: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
  };
  return <motion.div variants={variants} {...props} />;
}
