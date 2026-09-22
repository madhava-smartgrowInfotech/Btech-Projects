import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api, apiError } from "@/lib/api";
import { useI18n, type Language } from "@/lib/i18n";
import type { Settings } from "@/lib/types";

export type VoiceSource =
  | { kind: "payment"; id: number }
  | { kind: "sms"; id: number }
  | { kind: "collect"; id: number }
  | { kind: "qr-trick" }
  | { kind: "guide"; screen: string }
  | { kind: "text"; text: string };

interface SpeakResponse {
  url: string;
  text: string;
  lang: Language;
}

export function useSettings() {
  return useQuery({ queryKey: ["settings"], queryFn: async () => (await api.get<Settings>("/settings")).data, staleTime: 60_000 });
}

async function request(source: VoiceSource, lang: Language): Promise<SpeakResponse> {
  switch (source.kind) {
    case "payment":
      return (await api.post(`/voice/payment/${source.id}`, { lang })).data;
    case "sms":
      return (await api.post(`/voice/sms/${source.id}`, { lang })).data;
    case "collect":
      return (await api.post(`/voice/collect/${source.id}`, { lang })).data;
    case "qr-trick":
      return (await api.post(`/voice/qr-trick`, { lang })).data;
    case "guide":
      return (await api.get(`/voice/guide/${source.screen}`, { params: { lang } })).data;
    default:
      return (await api.post(`/voice/speak`, { text: source.text, lang })).data;
  }
}

const BCP47: Record<Language, string> = { en: "en-IN", hi: "hi-IN", te: "te-IN" };

function browserSpeak(text: string, lang: Language, onEnd: () => void): boolean {
  if (!("speechSynthesis" in window) || !text) return false;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = BCP47[lang];
  const voice = window.speechSynthesis.getVoices().find((v) => v.lang.toLowerCase().startsWith(lang));
  if (voice) u.voice = voice;
  u.onend = onEnd;
  u.onerror = onEnd;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
  return true;
}

/** Plays spoken warnings / guides from the API; falls back to the browser voice when offline. */
export function useVoice() {
  const { lang, t } = useI18n();
  const [playing, setPlaying] = useState<string | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const audio = useRef<HTMLAudioElement | null>(null);

  const stop = useCallback(() => {
    audio.current?.pause();
    audio.current = null;
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    setPlaying(null);
  }, []);

  useEffect(() => stop, [stop]);

  const speak = useCallback(
    async (key: string, source: VoiceSource, fallbackText?: string) => {
      stop();
      setLoading(key);
      try {
        const res = await request(source, lang);
        const el = new Audio(res.url);
        audio.current = el;
        el.onended = () => setPlaying(null);
        el.onerror = () => setPlaying(null);
        setPlaying(key);
        await el.play();
      } catch (err) {
        const detail = apiError(err);
        const text = fallbackText ?? (source.kind === "text" ? source.text : "");
        if (browserSpeak(text, lang, () => setPlaying(null))) {
          setPlaying(key);
        } else if (detail.code !== "error") {
          toast.message(t("voice.unavailable"), { description: detail.message });
        }
      } finally {
        setLoading(null);
      }
    },
    [lang, stop, t],
  );

  return { speak, stop, playing, loading };
}
