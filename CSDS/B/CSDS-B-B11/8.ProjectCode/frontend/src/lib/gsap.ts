import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

// Registered once here; every scroll-driven motion piece imports gsap from this module.
gsap.registerPlugin(ScrollTrigger);

export { gsap, ScrollTrigger };
