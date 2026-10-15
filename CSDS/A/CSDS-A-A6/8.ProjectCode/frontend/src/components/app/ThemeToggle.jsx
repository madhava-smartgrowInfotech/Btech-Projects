import { Moon, Sun } from "lucide-react";

import { IconButton } from "@/components/ui/Button";
import { useTheme } from "@/lib/theme";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const dark = resolvedTheme === "dark";
  return (
    <IconButton label={dark ? "Switch to light mode" : "Switch to dark mode"} onClick={() => setTheme(dark ? "light" : "dark")}>
      {dark ? <Moon /> : <Sun />}
    </IconButton>
  );
}
