import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Lang = "en" | "hi" | "mr";
export const LANGS: { value: Lang; label: string }[] = [
  { value: "en", label: "English" },
  { value: "hi", label: "हिन्दी" },
  { value: "mr", label: "मराठी" },
];

const KEY = "agrivision-lang";

/**
 * Key interface strings in English / Hindi / Marathi (the original Flask app only translated four phrases).
 * Anything not listed here, including disease and treatment text from the knowledge base, stays in English.
 */
const DICT: Record<string, { hi: string; mr: string }> = {
  "nav.dashboard": { hi: "डैशबोर्ड", mr: "डॅशबोर्ड" },
  "nav.detect": { hi: "रोग पहचान", mr: "रोग ओळख" },
  "nav.history": { hi: "इतिहास", mr: "इतिहास" },
  "nav.analytics": { hi: "विश्लेषण", mr: "विश्लेषण" },
  "nav.guide": { hi: "रोग गाइड", mr: "रोग मार्गदर्शक" },
  "nav.profile": { hi: "प्रोफ़ाइल", mr: "प्रोफाइल" },
  "nav.home": { hi: "मुख्य पृष्ठ", mr: "मुख्यपृष्ठ" },
  "common.signin": { hi: "लॉग इन", mr: "लॉग इन" },
  "common.signout": { hi: "लॉग आउट", mr: "लॉग आउट" },
  "common.getStarted": { hi: "शुरू करें", mr: "सुरू करा" },
  "common.newScan": { hi: "नई जांच", mr: "नवी तपासणी" },
  "common.exportCsv": { hi: "CSV निर्यात", mr: "CSV निर्यात" },
  "common.view": { hi: "देखें", mr: "पहा" },
  "common.delete": { hi: "हटाएँ", mr: "हटवा" },
  "common.save": { hi: "सहेजें", mr: "जतन करा" },
  "common.cancel": { hi: "रद्द करें", mr: "रद्द करा" },
  "common.search": { hi: "खोजें", mr: "शोधा" },
  "common.language": { hi: "भाषा", mr: "भाषा" },
  "hero.a": { hi: "फसल के रोग की पहचान", mr: "पिकाच्या रोगाची ओळख" },
  "hero.b": { hi: "दिनों में नहीं, सेकंडों में", mr: "दिवसांत नाही, सेकंदांत" },
  "hero.cta": { hi: "मुफ्त में जांच शुरू करें", mr: "मोफत तपासणी सुरू करा" },
  "hero.guide": { hi: "रोग गाइड", mr: "रोग मार्गदर्शक" },
  "detect.title": { hi: "पौधे के रोग की पहचान", mr: "वनस्पती रोग ओळखा" },
  "detect.crop": { hi: "फसल का प्रकार", mr: "पिकाचा प्रकार" },
  "detect.go": { hi: "निदान करें", mr: "निदान करा" },
  "detect.camera": { hi: "कैमरा", mr: "कॅमेरा" },
  "dash.hello": { hi: "नमस्ते", mr: "नमस्कार" },
  "dash.total": { hi: "कुल जांच", mr: "एकूण तपासण्या" },
  "dash.healthy": { hi: "स्वस्थ", mr: "निरोगी" },
  "dash.high": { hi: "गंभीर रोग", mr: "तीव्र रोग" },
  "dash.rate": { hi: "रोग दर", mr: "रोगाचे प्रमाण" },
  "dash.recent": { hi: "हाल की जांचें", mr: "अलीकडील तपासण्या" },
  "dash.quick": { hi: "त्वरित कार्य", mr: "झटपट कृती" },
  "dash.tips": { hi: "खेत के सुझाव", mr: "शेतातील टिप्स" },
  "history.title": { hi: "जांच का इतिहास", mr: "तपासणीचा इतिहास" },
  "analytics.title": { hi: "खेत विश्लेषण", mr: "शेती विश्लेषण" },
  "guide.title": { hi: "फसल रोग ज्ञानकोश", mr: "पीक रोग ज्ञानकोश" },
  "profile.title": { hi: "मेरी प्रोफ़ाइल", mr: "माझी प्रोफाइल" },
  "result.symptoms": { hi: "लक्षण", mr: "लक्षणे" },
  "result.lifecycle": { hi: "जीवन चक्र", mr: "जीवनचक्र" },
  "result.prevention": { hi: "रोकथाम", mr: "प्रतिबंध" },
  "result.treatments": { hi: "अनुशंसित उपचार", mr: "शिफारस केलेले उपचार" },
  "result.confidence": { hi: "AI विश्वसनीयता", mr: "AI विश्वासार्हता" },
  "result.top3": { hi: "शीर्ष-3 अनुमान", mr: "शीर्ष-3 अंदाज" },
};

interface LangValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  /** Translate a key; `fallback` is the English text. */
  t: (key: string, fallback: string) => string;
}

const LangContext = createContext<LangValue | null>(null);

function readStored(): Lang {
  try {
    const v = localStorage.getItem(KEY);
    return v === "hi" || v === "mr" ? v : "en";
  } catch {
    return "en";
  }
}

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(readStored);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((next: Lang) => {
    setLangState(next);
    try {
      localStorage.setItem(KEY, next);
    } catch {
      /* ignore */
    }
  }, []);

  const t = useCallback((key: string, fallback: string) => (lang === "en" ? fallback : (DICT[key]?.[lang] ?? fallback)), [lang]);
  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t]);
  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

export function useLang() {
  const ctx = useContext(LangContext);
  if (!ctx) throw new Error("useLang must be used inside <LangProvider>");
  return ctx;
}
