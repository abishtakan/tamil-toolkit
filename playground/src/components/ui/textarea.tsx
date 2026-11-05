import * as React from "react";
import { cn } from "../../lib/utils";

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          "w-full rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] px-4 py-3 text-base sm:text-lg font-tamil leading-[1.7] text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-semman)] disabled:cursor-not-allowed disabled:opacity-50 transition-all resize-y min-h-[140px]",
          className
        )}
        {...props}
      />
    );
  }
);
Textarea.displayName = "Textarea";
