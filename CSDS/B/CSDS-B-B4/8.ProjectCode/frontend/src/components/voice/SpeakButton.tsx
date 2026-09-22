import { useEffect, useId, useRef } from "react";
import { Loader2, Square, Volume2 } from "lucide-react";
import { Button, type ButtonProps } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";
import { useSettings, useVoice, type VoiceSource } from "@/lib/voice";
import { cn } from "@/lib/utils";

interface Props extends Omit<ButtonProps, "onClick"> {
  source: VoiceSource;
  label?: string;
  fallbackText?: string;
  /** Speak automatically once (respects the user's "speak warnings automatically" setting). */
  autoPlay?: boolean;
}

export function SpeakButton({ source, label, fallbackText, autoPlay = false, className, variant = "outline", size = "sm", ...rest }: Props) {
  const { t, lang } = useI18n();
  const { speak, stop, playing, loading } = useVoice();
  const settings = useSettings();
  const key = useId();
  const started = useRef<string | null>(null);
  const isPlaying = playing === key;
  const isLoading = loading === key;
  const sourceKey = JSON.stringify(source) + lang;

  useEffect(() => {
    if (!autoPlay || !settings.data) return;
    if (!settings.data.voice_enabled || !settings.data.auto_speak) return;
    if (started.current === sourceKey) return;
    started.current = sourceKey;
    void speak(key, source, fallbackText);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoPlay, settings.data, sourceKey]);

  if (settings.data && !settings.data.voice_enabled) return null;

  return (
    <Button
      type="button"
      variant={variant}
      size={size}
      className={cn("gap-2", isPlaying && "border-primary text-primary", className)}
      onClick={() => (isPlaying ? stop() : speak(key, source, fallbackText))}
      aria-pressed={isPlaying}
      {...rest}
    >
      {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : isPlaying ? <Square className="h-3.5 w-3.5 fill-current" /> : <Volume2 className="h-4 w-4" />}
      <span>{isPlaying ? t("common.stop") : label ?? t("common.listen")}</span>
      {isPlaying && (
        <span className="flex h-3 items-end gap-0.5" aria-hidden>
          {[0, 1, 2].map((i) => (
            <span key={i} className="w-0.5 animate-pulse rounded-full bg-current" style={{ height: `${6 + i * 3}px`, animationDelay: `${i * 120}ms` }} />
          ))}
        </span>
      )}
    </Button>
  );
}

/** Small "Guide me" button that speaks a screen's explanation in the chosen language. */
export function GuideButton({ screen, className }: { screen: string; className?: string }) {
  const { t } = useI18n();
  return <SpeakButton source={{ kind: "guide", screen }} label={t("common.guide")} variant="ghost" className={className} />;
}
