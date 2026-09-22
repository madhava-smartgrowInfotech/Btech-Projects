import { Toaster as Sonner } from "sonner";
import { useTheme } from "@/lib/theme";

export function Toaster() {
  const { resolved } = useTheme();
  return (
    <Sonner
      theme={resolved}
      position="top-center"
      richColors
      closeButton
      toastOptions={{ classNames: { toast: "rounded-xl border shadow-lg font-sans" } }}
    />
  );
}
