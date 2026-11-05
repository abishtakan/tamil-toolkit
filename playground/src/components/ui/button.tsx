import * as React from "react";
import { cn } from "../../lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "chip";
  size?: "sm" | "md" | "lg" | "icon";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-all duration-150 select-none disabled:opacity-50 disabled:pointer-events-none active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-semman)]",
          // Variants
          variant === "primary" &&
            "bg-[var(--color-semman)] text-[#faf7f2] hover:bg-[var(--color-semman-hover)] shadow-sm font-semibold",
          variant === "secondary" &&
            "bg-[var(--bg-raised)] text-[var(--color-mai)] hover:bg-[var(--border-line)] border border-[var(--border-line)]",
          variant === "outline" &&
            "border border-[var(--border-line)] text-[var(--color-mai)] hover:border-[var(--color-semman)] hover:text-[var(--color-semman)] bg-transparent",
          variant === "ghost" &&
            "text-[var(--color-muted)] hover:text-[var(--color-mai)] hover:bg-[var(--bg-raised)]",
          variant === "chip" &&
            "rounded-full border border-[var(--border-line)] bg-[var(--bg-surface)] text-[var(--color-muted)] hover:border-[var(--color-semman)] hover:text-[var(--color-semman)] data-[active=true]:bg-[var(--color-semman)] data-[active=true]:text-[#faf7f2] data-[active=true]:border-[var(--color-semman)]",
          // Sizes (strictly >= 44px touch targets on mobile)
          size === "sm" && "min-h-[36px] px-3 text-xs rounded-lg",
          size === "md" && "min-h-[44px] px-4 py-2 text-sm rounded-xl",
          size === "lg" && "min-h-[48px] px-6 py-3 text-base rounded-xl font-semibold",
          size === "icon" && "min-w-[44px] min-h-[44px] p-2 rounded-xl",
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
