import * as React from "react";
import { Copy, Check } from "lucide-react";
import { Button, ButtonProps } from "../ui/button";
import { useLanguage } from "../../lib/i18n";

export interface CopyButtonProps extends Omit<ButtonProps, "onClick"> {
  text: string;
  html?: string;
  onCopied?: () => void;
  label?: string;
  copiedLabel?: string;
}

export function CopyButton({
  text,
  html,
  onCopied,
  label,
  copiedLabel,
  variant = "primary",
  size = "md",
  className,
  ...props
}: CopyButtonProps) {
  const { t } = useLanguage();
  const [copied, setCopied] = React.useState(false);

  const displayLabel = label ?? t.actions.copy;
  const displayCopiedLabel = copiedLabel ?? t.actions.copied;

  const handleCopy = async () => {
    if (!text && !html) return;
    try {
      if (html && typeof ClipboardItem !== "undefined" && navigator.clipboard?.write) {
        const blobHtml = new Blob([html], { type: "text/html" });
        const blobText = new Blob([text || html], { type: "text/plain" });
        const item = new ClipboardItem({
          "text/html": blobHtml,
          "text/plain": blobText,
        });
        await navigator.clipboard.write([item]);
      } else {
        await navigator.clipboard.writeText(text);
      }
      setCopied(true);
      onCopied?.();
      setTimeout(() => setCopied(false), 2000);
    } catch {
      try {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        onCopied?.();
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error("Clipboard copy failed:", err);
      }
    }
  };

  return (
    <Button
      variant={variant}
      size={size}
      disabled={!text}
      onClick={handleCopy}
      className={className}
      aria-label={copied ? displayCopiedLabel : displayLabel}
      {...props}
    >
      {copied ? (
        <>
          <Check className="w-4 h-4 mr-1.5 text-[#faf7f2] animate-in zoom-in-50" />
          <span>{displayCopiedLabel}</span>
        </>
      ) : (
        <>
          <Copy className="w-4 h-4 mr-1.5" />
          <span>{displayLabel}</span>
        </>
      )}
    </Button>
  );
}
