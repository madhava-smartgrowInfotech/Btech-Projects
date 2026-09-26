import { Toaster as Sonner } from "sonner";
import { useTheme } from "@/lib/theme";

export function Toaster() {
  const { resolved } = useTheme();
  return (
    <Sonner
      theme={resolved}
      position="top-right"
      richColors
      closeButton
      toastOptions={{ classNames: { toast: "rounded-xl border shadow-lift font-sans" } }}
    />
  );
}
