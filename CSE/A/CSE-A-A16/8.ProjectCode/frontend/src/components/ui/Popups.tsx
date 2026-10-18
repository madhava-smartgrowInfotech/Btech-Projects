import { DropdownMenu, Popover as PopoverPrimitive, Tooltip as TooltipPrimitive } from "radix-ui";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export const TooltipProvider = TooltipPrimitive.Provider;

export function Tooltip({
  content,
  children,
  side = "top",
  className,
}: {
  content: ReactNode;
  children: ReactNode;
  side?: "top" | "bottom" | "left" | "right";
  className?: string;
}) {
  if (!content) return <>{children}</>;
  return (
    <TooltipPrimitive.Root>
      <TooltipPrimitive.Trigger asChild>{children}</TooltipPrimitive.Trigger>
      <TooltipPrimitive.Portal>
        <TooltipPrimitive.Content
          side={side}
          sideOffset={6}
          className={cn(
            "glass-strong z-[80] max-w-xs rounded-xl bg-popover px-3 py-2 text-xs text-popover-foreground data-[state=delayed-open]:animate-in data-[state=delayed-open]:fade-in-0 data-[state=delayed-open]:zoom-in-95",
            className,
          )}
        >
          {content}
        </TooltipPrimitive.Content>
      </TooltipPrimitive.Portal>
    </TooltipPrimitive.Root>
  );
}

export function Popover({
  trigger,
  children,
  align = "center",
  className,
  open,
  onOpenChange,
}: {
  trigger: ReactNode;
  children: ReactNode;
  align?: "start" | "center" | "end";
  className?: string;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}) {
  return (
    <PopoverPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <PopoverPrimitive.Trigger asChild>{trigger}</PopoverPrimitive.Trigger>
      <PopoverPrimitive.Portal>
        <PopoverPrimitive.Content
          align={align}
          sideOffset={8}
          collisionPadding={12}
          className={cn(
            "glass-strong z-[70] w-80 max-w-[calc(100vw-1.5rem)] rounded-2xl bg-popover p-4 text-sm text-popover-foreground outline-none data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
            className,
          )}
        >
          {children}
        </PopoverPrimitive.Content>
      </PopoverPrimitive.Portal>
    </PopoverPrimitive.Root>
  );
}

export interface MenuItem {
  label: ReactNode;
  icon?: ReactNode;
  onSelect: () => void;
  danger?: boolean;
  active?: boolean;
}

/** Dropdown menu (Radix): arrow keys, typeahead, Escape. */
export function Menu({
  trigger,
  items,
  header,
  align = "end",
  className,
}: {
  trigger: ReactNode;
  items: (MenuItem | "separator")[];
  header?: ReactNode;
  align?: "start" | "center" | "end";
  className?: string;
}) {
  return (
    <DropdownMenu.Root modal={false}>
      <DropdownMenu.Trigger asChild>{trigger}</DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align={align}
          sideOffset={8}
          className={cn(
            "glass-strong z-[70] min-w-48 rounded-2xl bg-popover p-1.5 text-sm text-popover-foreground data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
            className,
          )}
        >
          {header && <div className="px-2.5 py-2">{header}</div>}
          {header && <DropdownMenu.Separator className="my-1 h-px bg-[var(--glass-border)]" />}
          {items.map((item, i) =>
            item === "separator" ? (
              <DropdownMenu.Separator key={i} className="my-1 h-px bg-[var(--glass-border)]" />
            ) : (
              <DropdownMenu.Item
                key={i}
                onSelect={item.onSelect}
                className={cn(
                  "flex cursor-pointer select-none items-center gap-2.5 rounded-lg px-2.5 py-2 outline-none data-[highlighted]:bg-accent [&_svg]:size-4 [&_svg]:text-muted-foreground",
                  item.danger && "text-danger data-[highlighted]:bg-danger/10 [&_svg]:text-danger",
                  item.active && "font-semibold text-violet-ink",
                )}
              >
                {item.icon}
                {item.label}
              </DropdownMenu.Item>
            ),
          )}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
