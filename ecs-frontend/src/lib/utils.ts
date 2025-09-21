import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Format a power value given in kW into a human friendly string.
// < 1000 -> show in kW with 1 decimal; >= 1000 -> convert to MW with 1 decimal
export function formatPowerKw(valueKw: number | undefined | null): string {
  const v = typeof valueKw === 'number' ? valueKw : 0;
  if (Math.abs(v) >= 1000) {
    return `${(v / 1000).toFixed(1)} MW`;
  }
  return `${v.toFixed(1)} kW`;
}
