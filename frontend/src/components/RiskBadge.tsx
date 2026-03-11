import type { ReactNode } from "react";

type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

const styles: Record<Severity, string> = {
  LOW: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  MEDIUM: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  HIGH: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  CRITICAL: "bg-red-500/20 text-red-400 border-red-500/30",
};

interface RiskBadgeProps {
  level: Severity;
  children?: ReactNode;
}

export function RiskBadge({ level, children }: RiskBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${styles[level]}`}
    >
      {children ?? level}
    </span>
  );
}
