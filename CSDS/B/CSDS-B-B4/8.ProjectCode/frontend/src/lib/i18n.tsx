import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import en, { type MessageKey } from "@/locales/en";
import hi from "@/locales/hi";
import te from "@/locales/te";
import { storage } from "@/lib/storage";

export type Language = "en" | "hi" | "te";
export const LANGUAGES: { code: Language; label: string; native: string }[] = [
  { code: "en", label: "English", native: "English" },
  { code: "hi", label: "Hindi", native: "हिन्दी" },
  { code: "te", label: "Telugu", native: "తెలుగు" },
];

const dictionaries: Record<Language, Record<MessageKey, string>> = { en, hi, te };
const KEY = "upg.lang";

export type TParams = Record<string, string | number>;
export type TFunction = (key: MessageKey, params?: TParams) => string;

interface I18nState {
  lang: Language;
  setLang: (l: Language) => void;
  t: TFunction;
  /** Translate a key that arrives from the API (reason codes, scam types); falls back to the given text. */
  tx: (key: string, fallback?: string, params?: TParams) => string;
}

const I18nContext = createContext<I18nState | null>(null);

function interpolate(text: string, params?: TParams) {
  if (!params) return text;
  return text.replace(/\{(\w+)\}/g, (_, k: string) => (params[k] !== undefined ? String(params[k]) : `{${k}}`));
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Language>(() => {
    const saved = storage.get(KEY);
    return saved === "hi" || saved === "te" || saved === "en" ? saved : "en";
  });

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((l: Language) => {
    storage.set(KEY, l);
    setLangState(l);
  }, []);

  const t = useCallback<TFunction>(
    (key, params) => interpolate(dictionaries[lang][key] ?? en[key] ?? key, params),
    [lang],
  );

  const tx = useCallback(
    (key: string, fallback?: string, params?: TParams) => {
      const dict = dictionaries[lang] as Record<string, string>;
      const base = en as Record<string, string>;
      const text = dict[key] ?? base[key] ?? fallback ?? key;
      return interpolate(text, params);
    },
    [lang],
  );

  const value = useMemo(() => ({ lang, setLang, t, tx }), [lang, setLang, t, tx]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used inside I18nProvider");
  return ctx;
}
