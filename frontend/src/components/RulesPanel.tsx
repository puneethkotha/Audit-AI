import { Shield, ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import type { ComplianceRule } from "../types";
import { RiskBadge } from "./RiskBadge";

interface RulesPanelProps {
  rules: ComplianceRule[];
  isLoading: boolean;
}

export function RulesPanel({ rules, isLoading }: RulesPanelProps) {
  const [expanded, setExpanded] = useState(false);

  if (isLoading) {
    return (
      <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-6">
        <div className="flex items-center gap-2 text-[var(--text-muted)]">
          <Shield className="size-4 animate-pulse" />
          <span className="text-sm">Loading rules...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] overflow-hidden">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between p-4 text-left hover:bg-[var(--bg-elevated)]"
      >
        <div className="flex items-center gap-2">
          <Shield className="size-4 text-[var(--accent)]" />
          <span className="font-medium">Compliance rules</span>
          <span className="text-sm text-[var(--text-muted)]">
            ({rules.length} active)
          </span>
        </div>
        {expanded ? (
          <ChevronDown className="size-4 text-[var(--text-muted)]" />
        ) : (
          <ChevronRight className="size-4 text-[var(--text-muted)]" />
        )}
      </button>
      {expanded && (
        <div className="border-t border-[var(--border)] p-4">
          <div className="space-y-3">
            {rules.map((r) => (
              <div
                key={r.id}
                className="rounded-md border border-[var(--border)] bg-[var(--bg)] p-3"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-medium">{r.name}</span>
                  <RiskBadge
                    level={
                      r.severity as
                        | "LOW"
                        | "MEDIUM"
                        | "HIGH"
                        | "CRITICAL"
                    }
                  />
                  <span className="text-xs text-[var(--text-muted)]">
                    {r.category}
                  </span>
                </div>
                <div className="mt-1 text-xs text-[var(--text-muted)]">
                  {r.description}
                </div>
                <div className="mt-2 text-xs text-[var(--text-muted)]">
                  Field: <code className="rounded bg-[var(--bg-elevated)] px-1">{r.field}</code>
                  {r.value != null && (
                    <>
                      {" "}
                      | Value: <code className="rounded bg-[var(--bg-elevated)] px-1">{r.value}</code>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
