import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import type { ReviewOptions, Severity } from "@/lib/types";

/** Mirrors the Streamlit sidebar "Settings" expander. Kept in this browser only. */
export interface Settings {
  ml: boolean;
  minSeverity: Severity;
  useLlm: boolean;
  apiKey: string;
  ghToken: string;
}

const DEFAULTS: Settings = { ml: true, minSeverity: "info", useLlm: false, apiKey: "", ghToken: "" };
const KEY = "autosecai-settings";

function read(): Settings {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? { ...DEFAULTS, ...(JSON.parse(raw) as Partial<Settings>) } : DEFAULTS;
  } catch {
    return DEFAULTS;
  }
}

interface Ctx {
  settings: Settings;
  update: (patch: Partial<Settings>) => void;
  reset: () => void;
  /** Request options for the review endpoints. LLM explanations need a key (or one in the server env). */
  options: (llmEnv: boolean) => ReviewOptions;
}

const SettingsContext = createContext<Ctx | null>(null);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(read);

  const persist = useCallback((next: Settings) => {
    setSettings(next);
    try {
      localStorage.setItem(KEY, JSON.stringify(next));
    } catch {
      /* private mode: settings last for this visit only */
    }
  }, []);

  const value = useMemo<Ctx>(
    () => ({
      settings,
      update: (patch) => persist({ ...settings, ...patch }),
      reset: () => persist(DEFAULTS),
      options: (llmEnv) => ({
        ml: settings.ml,
        min_severity: settings.minSeverity,
        use_llm: settings.useLlm && (Boolean(settings.apiKey) || llmEnv),
        api_key: settings.apiKey || null,
        gh_token: settings.ghToken || null,
      }),
    }),
    [settings, persist],
  );
  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings() {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used inside SettingsProvider");
  return ctx;
}
