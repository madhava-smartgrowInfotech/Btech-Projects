import { motion } from "framer-motion";
import { ScanEye } from "lucide-react";

// Real sample image served by the API (no sign-in needed for sample files).
const SAMPLE = "/api/samples/0000122e.png";

const STEPS = [
  "Green channel",
  "CLAHE contrast",
  "2-level Haar wavelets",
  "LeNet CNN",
  "Grad-CAM heatmap",
  "SHAP risk factors",
  "Combined risk stage",
];

/** The screening pipeline shown next to the hero: a real fundus sample and the steps it goes through. */
export function ExamplePipeline() {
  return (
    <div className="relative mx-auto w-full max-w-md">
      <div aria-hidden className="absolute -inset-8 rounded-[2.5rem] bg-grad-primary opacity-25 blur-3xl" />
      <div className="glass-strong sweep relative space-y-4 rounded-3xl p-4 sm:p-5">
        <div className="flex items-center gap-2 border-b border-[var(--glass-border)] pb-3 text-xs text-muted-foreground">
          <ScanEye className="size-4 text-violet-ink" aria-hidden /> Fundus screening · sample image
        </div>
        <img
          src={SAMPLE}
          alt="Sample retinal fundus photograph from the held-out test split"
          className="aspect-square w-full rounded-2xl bg-black object-cover"
          onError={(e) => {
            e.currentTarget.style.display = "none";
          }}
        />
        <ol className="grid grid-cols-2 gap-2 text-xs">
          {STEPS.map((step, i) => (
            <motion.li
              key={step}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + i * 0.12, duration: 0.45 }}
              className="flex items-center gap-2 rounded-xl border border-[var(--glass-border)] bg-[var(--glass)] px-2.5 py-2"
            >
              <span className="grid size-5 shrink-0 place-items-center rounded-md bg-grad-primary text-[10px] font-semibold text-white">{i + 1}</span>
              <span className="truncate">{step}</span>
            </motion.li>
          ))}
        </ol>
      </div>
    </div>
  );
}
