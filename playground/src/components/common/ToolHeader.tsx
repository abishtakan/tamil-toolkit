import * as React from "react";

export interface ToolHeaderProps {
  title: string;
  description: string;
  actions?: React.ReactNode;
  meta?: React.ReactNode;
}

export function ToolHeader({ title, description, actions, meta }: ToolHeaderProps) {
  return (
    <header className="pb-5 border-b border-[var(--border-line)] space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div className="space-y-1.5 min-w-0">
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-2xl sm:text-[26px] font-tamil font-bold tracking-tight text-[var(--color-mai)] leading-snug">
              {title}
            </h1>
            {meta}
          </div>
          <p className="text-sm text-[var(--color-muted)] font-tamil-sans leading-relaxed max-w-2xl">
            {description}
          </p>
        </div>

        {actions && (
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            {actions}
          </div>
        )}
      </div>
    </header>
  );
}
