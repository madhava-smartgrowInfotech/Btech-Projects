import { create } from "zustand";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, XCircle, Info, X } from "lucide-react";
import { cn } from "@/lib/format";

type ToastTone = "success" | "error" | "info";
interface ToastItem {
  id: number;
  tone: ToastTone;
  title: string;
  description?: string;
}

interface ToastState {
  toasts: ToastItem[];
  push: (t: Omit<ToastItem, "id">) => void;
  dismiss: (id: number) => void;
}

let counter = 0;

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  push: (t) =>
    set((s) => {
      const id = ++counter;
      setTimeout(() => useToastStore.getState().dismiss(id), 4200);
      return { toasts: [...s.toasts, { ...t, id }] };
    }),
  dismiss: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

export const toast = {
  success: (title: string, description?: string) => useToastStore.getState().push({ tone: "success", title, description }),
  error: (title: string, description?: string) => useToastStore.getState().push({ tone: "error", title, description }),
  info: (title: string, description?: string) => useToastStore.getState().push({ tone: "info", title, description }),
};

const ICONS: Record<ToastTone, typeof CheckCircle2> = { success: CheckCircle2, error: XCircle, info: Info };
const TONE_CLASSES: Record<ToastTone, string> = {
  success: "border-brand-200 text-brand-700",
  error: "border-rose-200 text-rose-700",
  info: "border-sky-200 text-sky-700",
};

export function Toaster() {
  const toasts = useToastStore((s) => s.toasts);
  const dismiss = useToastStore((s) => s.dismiss);

  return (
    <div className="fixed bottom-5 right-5 z-[100] flex flex-col gap-2 w-[340px] max-w-[90vw]">
      <AnimatePresence>
        {toasts.map((t) => {
          const Icon = ICONS[t.tone];
          return (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: 12, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 24, scale: 0.96 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
              className={cn("flex items-start gap-2.5 rounded-xl border bg-white/95 backdrop-blur px-3.5 py-3 shadow-lg", TONE_CLASSES[t.tone])}
            >
              <Icon size={18} className="mt-0.5 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-ink-900">{t.title}</p>
                {t.description && <p className="text-xs text-ink-500 mt-0.5">{t.description}</p>}
              </div>
              <button onClick={() => dismiss(t.id)} className="text-ink-400 hover:text-ink-700">
                <X size={15} />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
