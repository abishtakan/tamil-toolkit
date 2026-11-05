import * as React from "react";
import { cn } from "../../lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "terracotta" | "sandhanam" | "outline" | "mono";
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium font-tamil-sans transition-colors",
        variant === "default" && "bg-[var(--bg-raised)] text-[var(--color-mai)] border border-[var(--border-line)]",
        variant === "terracotta" && "bg-[var(--color-semman-light)] text-[var(--color-semman)] border border-[var(--color-semman)]/30 font-semibold",
        variant === "sandhanam" && "bg-[var(--color-sandhanam-light)] text-[var(--color-sandhanam)] border border-[var(--color-sandhanam)]/30",
        variant === "outline" && "border border-[var(--border-line)] text-[var(--color-muted)]",
        variant === "mono" && "font-mono-tamil text-[11px] bg-[var(--bg-raised)] text-[var(--color-mai)] border border-[var(--border-line)] px-2 py-0.5",
        className
      )}
      {...props}
    />
  );
}
