import { Check, ChevronDown } from "lucide-react";
import { Select as S } from "radix-ui";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export interface SelectOption {
  value: string;
  label: ReactNode;
  description?: ReactNode;
  disabled?: boolean;
}

/** Glass select built on Radix (keyboard, typeahead and Escape handled). */
export function Select({
  value,
  onValueChange,
  options,
  placeholder = "Choose…",
  icon,
  id,
  className,
  disabled,
  "aria-label": ariaLabel,
  "aria-describedby": describedBy,
}: {
  value: string | undefined;
  onValueChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  icon?: ReactNode;
  id?: string;
  className?: string;
  disabled?: boolean;
  "aria-label"?: string;
  "aria-describedby"?: string;
}) {
  // "" keeps Radix controlled while still showing the placeholder
  return (
    <S.Root value={value ?? ""} onValueChange={onValueChange} disabled={disabled}>
      <div className={cn("field", className)}>
        <S.Trigger
          id={id}
          aria-label={ariaLabel}
          aria-describedby={describedBy}
          className="field-inner flex h-10 w-full items-center gap-2 px-3 text-left text-sm text-foreground outline-none data-[placeholder]:text-muted-foreground disabled:opacity-60"
        >
          {icon && <span className="text-muted-foreground [&_svg]:size-4">{icon}</span>}
          <span className="min-w-0 flex-1 truncate">
            <S.Value placeholder={placeholder} />
          </span>
          <S.Icon>
            <ChevronDown className="size-4 text-muted-foreground" />
          </S.Icon>
        </S.Trigger>
      </div>
      <S.Portal>
        <S.Content
          position="popper"
          sideOffset={6}
          className="glass-strong z-[70] max-h-[min(22rem,var(--radix-select-content-available-height))] min-w-[var(--radix-select-trigger-width)] overflow-hidden rounded-xl bg-popover p-1 text-sm data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95"
        >
          <S.Viewport className="scrollbar-thin">
            {options.map((o) => (
              <S.Item
                key={o.value}
                value={o.value}
                disabled={o.disabled}
                className="relative flex cursor-pointer select-none items-start gap-2 rounded-lg py-2 pl-8 pr-3 outline-none data-[disabled]:pointer-events-none data-[highlighted]:bg-accent data-[disabled]:opacity-50"
              >
                <S.ItemIndicator className="absolute left-2.5 top-2.5">
                  <Check className="size-4 text-violet-ink" />
                </S.ItemIndicator>
                <div className="min-w-0">
                  <S.ItemText>{o.label}</S.ItemText>
                  {o.description && <div className="text-xs text-muted-foreground">{o.description}</div>}
                </div>
              </S.Item>
            ))}
          </S.Viewport>
        </S.Content>
      </S.Portal>
    </S.Root>
  );
}
