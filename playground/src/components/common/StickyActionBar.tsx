import { CopyButton } from "./CopyButton";
import { Button } from "../ui/button";
import { useLanguage } from "../../lib/i18n";
import { ArrowLeftRight, Trash2 } from "lucide-react";

export interface StickyActionBarProps {
  outputText: string;
  onClear: () => void;
  onSwap?: () => void;
  copyLabel?: string;
  copiedLabel?: string;
  clearLabel?: string;
  swapLabel?: string;
}

export function StickyActionBar({
  outputText,
  onClear,
  onSwap,
  copyLabel,
  copiedLabel,
  clearLabel,
  swapLabel
}: StickyActionBarProps) {
  const { t } = useLanguage();

  const dCopy = copyLabel ?? t.actions.copy;
  const dCopied = copiedLabel ?? t.actions.copied;
  const dClear = clearLabel ?? t.actions.clear;
  const dSwap = swapLabel ?? t.actions.swap;

  return (
    <aside
      aria-label="Mobile quick actions"
      className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-[var(--bg-surface)]/95 backdrop-blur-md border-t border-[var(--border-line)] px-4 py-3 shadow-lg"
      style={{ paddingBottom: "max(12px, env(safe-area-inset-bottom))" }}
    >
      <div className="flex items-center justify-between gap-2 max-w-lg mx-auto">
        {onSwap && (
          <Button
            variant="outline"
            size="md"
            onClick={onSwap}
            className="flex-1 text-xs sm:text-sm font-tamil"
          >
            <ArrowLeftRight className="w-4 h-4 mr-1 text-[var(--color-semman)]" />
            <span>{dSwap}</span>
          </Button>
        )}

        <Button
          variant="outline"
          size="md"
          onClick={onClear}
          className="px-3.5 text-xs text-[var(--color-muted)] hover:text-red-600 font-tamil"
          aria-label={dClear}
        >
          <Trash2 className="w-4 h-4 mr-1" />
          <span>{dClear}</span>
        </Button>

        <CopyButton
          text={outputText}
          label={dCopy}
          copiedLabel={dCopied}
          variant="primary"
          size="md"
          className="flex-1 text-xs sm:text-sm"
        />
      </div>
    </aside>
  );
}
