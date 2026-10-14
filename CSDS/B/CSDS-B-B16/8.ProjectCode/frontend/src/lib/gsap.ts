import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

// One place registers the plugin, so every motion component shares the same ScrollTrigger.
gsap.registerPlugin(ScrollTrigger);

export { gsap, ScrollTrigger };
