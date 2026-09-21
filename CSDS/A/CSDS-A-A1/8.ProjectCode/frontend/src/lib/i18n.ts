import type { Language } from "@/lib/types";

export const LANGUAGES: { code: Language; name: string; native: string }[] = [
  { code: "en", name: "English", native: "English" },
  { code: "hi", name: "Hindi", native: "हिन्दी" },
  { code: "te", name: "Telugu", native: "తెలుగు" },
];

export function languageLabel(code: string) {
  const lang = LANGUAGES.find((l) => l.code === code);
  return lang ? `${lang.native}${lang.code !== "en" ? ` (${lang.name})` : ""}` : code;
}
