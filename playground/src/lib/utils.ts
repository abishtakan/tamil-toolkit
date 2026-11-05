import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatExecutionTime(ms: number): string {
  if (ms < 1) {
    return "< 1 ms";
  }
  return `${ms.toFixed(1)} ms`;
}
