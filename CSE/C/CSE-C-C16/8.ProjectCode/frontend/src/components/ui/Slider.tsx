import { useId } from "react";

import { cn } from "@/lib/utils";

/** Labelled range slider with a gradient fill (native input, so keyboard and screen readers just work). */
export function Slider({
  label,
  value,
  onChange,
  min,
  max,
  step = 1,
  hint,
  disabled,
  className,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
  hint?: string;
  disabled?: boolean;
  className?: string;
}) {
  const id = useId();
  const fill = ((value - min) / (max - min)) * 100;
  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-baseline justify-between gap-3">
        <label htmlFor={id} className="text-sm font-medium text-foreground/90">
          {label}
        </label>
        <output htmlFor={id} className="font-display text-sm font-semibold tabular-nums text-violet-ink">
          {value.toLocaleString("en-US")}
        </output>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-describedby={hint ? `${id}-hint` : undefined}
        className="h-2 w-full cursor-pointer appearance-none rounded-full disabled:cursor-not-allowed disabled:opacity-50 [&::-moz-range-thumb]:size-5 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-white [&::-moz-range-thumb]:bg-[var(--violet)] [&::-webkit-slider-thumb]:size-5 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-white [&::-webkit-slider-thumb]:bg-[var(--violet)] [&::-webkit-slider-thumb]:shadow-[0_0_14px_rgba(34,160,107,0.7)]"
        style={{
          background: `linear-gradient(90deg, var(--violet), var(--cyan)) 0 / ${fill}% 100% no-repeat, var(--muted)`,
        }}
      />
      <div className="flex justify-between text-[11px] text-muted-foreground tabular-nums">
        <span>{min.toLocaleString("en-US")}</span>
        <span>{max.toLocaleString("en-US")}</span>
      </div>
      {hint && (
        <p id={`${id}-hint`} className="text-xs text-muted-foreground">
          {hint}
        </p>
      )}
    </div>
  );
}
