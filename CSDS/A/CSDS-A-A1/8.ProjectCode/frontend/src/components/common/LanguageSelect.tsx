import { Languages } from "lucide-react";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { LANGUAGES } from "@/lib/i18n";
import type { Language } from "@/lib/types";
import { cn } from "@/lib/utils";

export function LanguageSelect({
  value,
  onChange,
  className,
  label = "Answer language",
}: {
  value: Language;
  onChange: (lang: Language) => void;
  className?: string;
  label?: string;
}) {
  return (
    <Select value={value} onValueChange={(v) => onChange(v as Language)}>
      <SelectTrigger className={cn("w-[150px]", className)} aria-label={label}>
        <Languages className="size-4 text-muted-foreground" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {LANGUAGES.map((l) => (
          <SelectItem key={l.code} value={l.code}>
            {l.native}
            {l.code !== "en" && <span className="text-muted-foreground"> · {l.name}</span>}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
