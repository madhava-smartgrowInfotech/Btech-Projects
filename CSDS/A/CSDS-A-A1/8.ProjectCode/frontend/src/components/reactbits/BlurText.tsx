/*
 * BlurText - words fade in from a blur, one after another (React Bits component, Motion version,
 * adapted: renders plain text instantly when the user prefers reduced motion).
 */
import { motion, useReducedMotion } from "motion/react";
import { useEffect, useRef, useState, type ElementType } from "react";

interface BlurTextProps {
  text: string;
  delay?: number;
  className?: string;
  as?: ElementType;
  direction?: "top" | "bottom";
  stepDuration?: number;
  highlight?: string[];
  highlightClassName?: string;
}

export default function BlurText({
  text,
  delay = 90,
  className = "",
  as: Tag = "p",
  direction = "top",
  stepDuration = 0.35,
  highlight = [],
  highlightClassName = "",
}: BlurTextProps) {
  const words = text.split(" ");
  const ref = useRef<HTMLElement>(null);
  const [inView, setInView] = useState(false);
  const reduce = useReducedMotion();

  useEffect(() => {
    if (!ref.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1 },
    );
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  const from = { filter: "blur(10px)", opacity: 0, y: direction === "top" ? -40 : 40 };
  const mid = { filter: "blur(5px)", opacity: 0.5, y: direction === "top" ? 5 : -5 };
  const to = { filter: "blur(0px)", opacity: 1, y: 0 };

  if (reduce) {
    return <Tag className={className}>{text}</Tag>;
  }

  return (
    <Tag ref={ref} className={className} aria-label={text}>
      {words.map((word, i) => (
        <motion.span
          key={`${word}-${i}`}
          aria-hidden="true"
          className={`inline-block will-change-[transform,filter,opacity] ${highlight.includes(word) ? highlightClassName : ""}`}
          initial={from}
          animate={inView ? { filter: [from.filter, mid.filter, to.filter], opacity: [0, 0.5, 1], y: [from.y, mid.y, 0] } : from}
          transition={{ duration: stepDuration * 2, times: [0, 0.5, 1], delay: (i * delay) / 1000, ease: "easeOut" }}
        >
          {word}
          {i < words.length - 1 && " "}
        </motion.span>
      ))}
    </Tag>
  );
}
